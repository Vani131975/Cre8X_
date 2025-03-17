from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from bson import ObjectId
import uuid
import json
from datetime import datetime

from db_connection import accounts_collection, MongoDBConnector

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    skills = models.ManyToManyField('Skill', related_name='users')
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    reported_count = models.PositiveIntegerField(default=0)
    is_warned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mongo_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

    def add_report(self):
        self.reported_count += 1
        if self.reported_count >= 3:
            self.is_warned = True
        self.save()
    
    def to_mongo_dict(self):
        """Convert user instance to MongoDB document"""
        user_skills = [skill.to_dict() for skill in self.skills.all()]
        profile_image_path = str(self.profile_image) if self.profile_image else None
        return {
            'django_id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'bio': self.bio,
            'profile_image': profile_image_path,
            'reported_count': self.reported_count,
            'is_warned': self.is_warned,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'is_active': self.is_active,
            'date_joined': self.date_joined.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'skills': user_skills,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    
    def save_to_mongodb(self):
       """Save user to MongoDB"""
       user_data = self.to_mongo_dict()

       if self.mongo_id:
           try:
               mongo_obj_id = ObjectId(self.mongo_id)  
           except Exception:
               print(f"❌ Invalid Mongo ID: {self.mongo_id}")
               return  

           update_result = accounts_collection.update_one(
               {'_id': mongo_obj_id},  
               {'$set': user_data}
           )
           print(f"✅ MongoDB Update Result: {update_result.modified_count}")
       else:
           result = accounts_collection.insert_one(user_data)
           self.mongo_id = str(result.inserted_id) 
           self.save(update_fields=["mongo_id"])  
           print(f"🚀 Inserted New MongoDB Record: {self.mongo_id}")
 
    
    
    @classmethod
    def from_mongo(cls, mongo_id):
        """Get user data from MongoDB by mongo_id"""
        user_data = accounts_collection.find_one({'_id': mongo_id})
        if not user_data:
            return None
 
        try:
            user = cls.objects.get(mongo_id=str(mongo_id))
            return user
        except cls.DoesNotExist:
            return None

@receiver(post_save, sender=CustomUser.skills.through)
def sync_skills_to_mongodb(sender, instance, action, **kwargs):
    """Update MongoDB when skills are added/removed"""
    if action in ["post_add", "post_remove", "post_clear"]:  
        user = instance 
        print(f"Syncing skills for: {user.username}")
        user.save_to_mongodb()

@receiver(post_delete, sender=CustomUser)
def delete_from_mongodb(sender, instance, **kwargs):
    """Delete user from MongoDB when deleted from Django"""
    if instance.mongo_id:
        accounts_collection.delete_one({'_id': instance.mongo_id})