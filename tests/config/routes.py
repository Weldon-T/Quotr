"""所有已知路由常量。"""

# 认证
SIGN_IN = "/auth/sign-in"
SIGN_UP = "/auth/sign-up?step=profile"
RESET_PASSWORD = "/auth/reset-password?action=input-email"

# Dashboard 模块
PROJECT_LIST = "/dashboard/project"
PROJECT_DETAIL = "/dashboard/project/{id}"
DATABASE = "/dashboard/database"
TEMPLATE = "/dashboard/template"
SUPPLIERS = "/dashboard/suppliers/manage"

# API 端点
API_SIGNIN = "/api/auth/v2/signin"
API_SIGN_OUT_REASON = "/api/auth/v2/sign-out-reason"
API_QUERY_ORG = "/api/query-org"
API_GET_PROJECTS = "/api/get-projects"
API_GET_VERSIONS = "/api/get-versions"
API_GET_ROOM_TYPES = "/api/get-roomTypes"
API_GET_CUSTOMER_TEMPLATES = "/api/get-customer-templates"
API_GET_DEFAULT_TEMPLATES = "/api/get-default-templates"
API_GET_CUSTOMER_SUPPLIER_LIST = "/api/get-customer-supplier-list"
API_MEETINGS = "/api/qms/v1/meetings"
API_BELL = "/api/qms/v1/bell"
API_GET_UNREAD_COUNT = "/api/get-unread-count"

# 所有需要认证的 API（用于未认证访问测试）
PROTECTED_APIS = [
    API_QUERY_ORG,
    API_GET_PROJECTS,
    API_GET_VERSIONS,
    API_GET_ROOM_TYPES,
    API_GET_CUSTOMER_TEMPLATES,
    API_GET_DEFAULT_TEMPLATES,
    API_GET_CUSTOMER_SUPPLIER_LIST,
    API_MEETINGS,
    API_BELL,
    API_GET_UNREAD_COUNT,
]

# localStorage 关键字段
LS_AUTH_SESSION = "auth_v2_session"
LS_TOKEN = "token"
LS_USER = "user"
LS_ORGANIZATION = "organization"
LS_ONBOARDING = "quotr_onboarding_state"
LS_SELECTED_TEMPLATE = "selectedTemplate"
LS_LAST_WORKSPACE = "quotr:last-workspace-org-id"

LS_REQUIRED_FIELDS = [LS_AUTH_SESSION, LS_TOKEN, LS_USER, LS_ORGANIZATION]
