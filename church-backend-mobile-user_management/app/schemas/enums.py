from enum import Enum

class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"                 # Lead Pastor
    PASTOR_STAFF = "PASTOR_STAFF"   # Pastor / Staff
    TEACHING_TEAM = "TEACHING_TEAM" # Teaching Team
    COMMUNICATIONS_TEAM = "COMMUNICATIONS_TEAM" # Communications Team
    SMALL_GROUP_LEADER = "SMALL_GROUP_LEADER"   # Small Group Leader
