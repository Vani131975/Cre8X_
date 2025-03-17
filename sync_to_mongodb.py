# sync_to_mongodb.py
# Run this script with: python manage.py shell < sync_to_mongodb.py

from accounts.models import CustomUser, Skill
from projects.models import Project 
from notifications.models import Notification 
from db_connection import accounts_collection, projects_collection, notifications_collection

def sync_users_to_mongodb():
    print("Syncing users to MongoDB...")
    count = 0
    users = CustomUser.objects.all()

    if not users:
        print("No users found in the database.")
        return

    for user in users:
        user.save_to_mongodb()
        count += 1
    
    print(f"Synced {count} users to MongoDB")


def sync_projects_to_mongodb():
    print("Syncing projects to MongoDB...")
    count = 0
    projects = Project.objects.all()
    for project in projects:
        project_data = {
            'django_id': project.id,
            'title': project.title,
            'description': project.description,
            'created_by': {
                'id': project.created_by.id,
                'username': project.created_by.username,
                'mongo_id': project.created_by.mongo_id
            },
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat() if hasattr(project, 'updated_at') else None,
            'team_members': [
                {
                    'id': member.user.id,
                    'username': member.user.username,
                    'mongo_id': member.user.mongo_id,
                    'role': member.role
                } for member in project.team_members.all()
            ]
        }
        result = projects_collection.insert_one(project_data)
        if hasattr(project, 'mongo_id'):
            project.mongo_id = str(result.inserted_id)
            project.save(update_fields=['mongo_id'])
        count += 1
    print(f"Synced {count} projects to MongoDB")

if __name__ == "__main__":
    sync_users_to_mongodb()
    # Uncomment to sync projects too
    sync_projects_to_mongodb()
    
    print("MongoDB sync complete!")