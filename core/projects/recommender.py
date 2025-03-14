class ProjectRecommender:
    """
    A simple AI recommender system to match users with projects based on skills.
    In a real-world scenario, you might use a more sophisticated ML model.
    """
    @staticmethod
    def get_skill_match_score(user_skills, required_skills):
        """
        Calculate a match score based on skill overlap.
        Returns a value between 0 and 1, where 1 is a perfect match.
        """
        if not required_skills:
            return 0
            
        user_skill_set = set(user_skills)
        required_skill_set = set(required_skills)
        
        # Calculate the overlap
        matching_skills = user_skill_set.intersection(required_skill_set)
        
        # Calculate match score
        match_score = len(matching_skills) / len(required_skill_set)
        
        return match_score
    
    @staticmethod
    def recommend_users_for_project(project, users=None, top_n=5):
        """
        Recommend users who are good matches for a project based on skills.
        
        Args:
            project: The project object
            users: Optional list of users to consider. If None, all users are considered.
            top_n: Number of top recommendations to return
            
        Returns:
            List of (user, score) tuples, sorted by score descending
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get required skills for the project
        required_skills = list(project.required_skills.values_list('name', flat=True))
        
        # Get all users if not specified
        if users is None:
            # Exclude project creator and users already in the project
            users = User.objects.exclude(
                id=project.created_by.id
            ).exclude(
                joined_projects__project=project
            )
        
        user_scores = []
        
        for user in users:
            # Get user skills
            user_skills = list(user.skills.values_list('name', flat=True))
            
            # Calculate match score
            score = ProjectRecommender.get_skill_match_score(user_skills, required_skills)
            
            # Apply penalty for reported users
            if user.reported_count > 0:
                penalty = min(0.5, user.reported_count * 0.1)  # Max 50% penalty
                score = max(0, score - penalty)
            
            user_scores.append((user, score))
        
        # Sort by score descending and get top N
        user_scores.sort(key=lambda x: x[1], reverse=True)
        return user_scores[:top_n]
    
    @staticmethod
    def recommend_projects_for_user(user, projects=None, top_n=5):
        """
        Recommend projects that match a user's skills.
        
        Args:
            user: The user object
            projects: Optional list of projects to consider. If None, all active projects are considered.
            top_n: Number of top recommendations to return
            
        Returns:
            List of (project, score) tuples, sorted by score descending
        """
        from projects.models import Project
        
        # Get user skills
        user_skills = list(user.skills.values_list('name', flat=True))
        
        # Get all active projects if not specified
        if projects is None:
            # Exclude projects created by user or already joined by user
            projects = Project.objects.filter(
                status='active'
            ).exclude(
                created_by=user
            ).exclude(
                team_members__user=user
            )
        
        project_scores = []
        
        for project in projects:
            # Get required skills for the project
            required_skills = list(project.required_skills.values_list('name', flat=True))
            
            # Calculate match score
            score = ProjectRecommender.get_skill_match_score(user_skills, required_skills)
            
            project_scores.append((project, score))
        
        # Sort by score descending and get top N
        project_scores.sort(key=lambda x: x[1], reverse=True)
        return project_scores[:top_n]