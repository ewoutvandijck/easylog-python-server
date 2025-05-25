# Client Agent Configuration Guide

## Overview

This Python environment provides a highly flexible agent framework for building customized AI solutions for different clients. The modular architecture allows for extensive configuration of agents, tools, roles, and workflows to meet specific client requirements across various industries and use cases.

## Core Configuration Architecture

### Agent Configuration Patterns

The system supports multiple configuration approaches for different client needs:

#### 1. Role-Based Configuration

Each agent can have multiple roles with specific behaviors, tools, and permissions:

```python
class ClientAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            # Customer Service Role
            RoleConfig(
                name="CustomerSupport",
                prompt="You are a helpful customer service representative...",
                model="anthropic/claude-sonnet-4",
                tools_regex="tool_(search_documents|send_notification|create_.*_chart).*",
                allowed_subjects=["FAQ", "Policies", "Products"],
                questionaire=[
                    QuestionaireQuestionConfig(
                        question="What is your customer ID?",
                        name="customer_id",
                        instructions="Validate against customer database"
                    )
                ],
            ),
            # Technical Support Role
            RoleConfig(
                name="TechnicalSupport",
                prompt="You are a technical support specialist...",
                model="openai/gpt-4.1",
                tools_regex="tool_(easylog_sql|search_documents|create_bar_chart).*",
                allowed_subjects=["Technical", "Troubleshooting"],
                questionaire=[],
            ),
            # Manager/Supervisor Role
            RoleConfig(
                name="Supervisor",
                prompt="You are a supervisor with access to all tools...",
                model="anthropic/claude-sonnet-4",
                tools_regex=".*",  # All tools
                allowed_subjects=None,  # All subjects
                questionaire=[],
            )
        ]
    )
    prompt: str = Field(
        default="Client: {client_name}\\nRole: {current_role}\\nInstructions: {current_role_prompt}"
    )
```

#### 2. Industry-Specific Configurations

**Healthcare/Medical (MUMC-style)**:

```python
class HealthcareAgentConfig(BaseModel):
    roles: list[RoleConfig] = [
        RoleConfig(
            name="HealthcareAssistant",
            prompt="You are a medical assistant specialized in COPD care...",
            model="anthropic/claude-sonnet-4",  # High accuracy for medical
            tools_regex="tool_(create_zlm_chart|search_documents|send_notification).*",
            allowed_subjects=["COPD", "Medical_Guidelines", "Patient_Care"],
            questionaire=[
                QuestionaireQuestionConfig(
                    question="What is your patient ID?",
                    name="patient_id",
                    instructions="Validate patient access permissions"
                )
            ],
        )
    ]
```

**Business Intelligence/Analytics**:

```python
class BusinessAgentConfig(BaseModel):
    roles: list[RoleConfig] = [
        RoleConfig(
            name="DataAnalyst",
            prompt="You are a business intelligence analyst...",
            model="openai/gpt-4.1",
            tools_regex="tool_(easylog_sql|create_.*_chart|easylog_backend).*",
            allowed_subjects=["Analytics", "KPIs", "Reports"],
            questionaire=[
                QuestionaireQuestionConfig(
                    question="Which department are you analyzing?",
                    name="department",
                    instructions="Used for data filtering"
                )
            ],
        )
    ]
```

**Customer Service/Support**:

```python
class CustomerServiceConfig(BaseModel):
    roles: list[RoleConfig] = [
        RoleConfig(
            name="SupportAgent",
            prompt="You are a friendly customer support agent...",
            model="openai/gpt-4.1-mini",  # Cost-effective for high volume
            tools_regex="tool_(search_documents|ask_multiple_choice|send_notification).*",
            allowed_subjects=["FAQ", "Policies", "Product_Info"],
            questionaire=[
                QuestionaireQuestionConfig(
                    question="Please provide your order number",
                    name="order_number",
                    instructions="Validate order existence"
                )
            ],
        )
    ]
```

## Tool Configuration Matrix

### Available Tool Categories

#### 1. Data Access Tools

**EasyLog Backend Tools**:

```python
# Configuration for client-specific API access
easylog_backend_tools = EasylogBackendTools(
    bearer_token=client_specific_token,
    base_url=client_api_endpoint,
)

# Available tools:
- tool_easylog_backend_get_companies
- tool_easylog_backend_get_users
- tool_easylog_backend_get_user_info
- tool_easylog_backend_create_user
- tool_easylog_backend_update_user
- tool_easylog_backend_delete_user
- tool_easylog_backend_get_projects
- tool_easylog_backend_create_project
- tool_easylog_backend_update_project
- tool_easylog_backend_delete_project
```

**SQL Database Tools**:

```python
# Configuration for client database access
easylog_sql_tools = EasylogSqlTools(
    ssh_key_path=client_ssh_key,
    ssh_host=client_db_host,
    ssh_username=client_username,
    db_password=client_db_password,
    db_user=client_db_user,
    db_host=client_internal_db_host,
    db_port=client_db_port,
    db_name=client_database_name,
)

# Available tools:
- tool_easylog_sql_query_database
- tool_easylog_sql_get_table_schema
- tool_easylog_sql_get_all_tables
```

#### 2. Visualization Tools

**Chart Creation Tools**:

```python
# Industry-specific chart configurations
def configure_charts_for_client(industry: str):
    if industry == "healthcare":
        return {
            "primary_chart": "tool_create_zlm_chart",  # COPD-specific
            "secondary_charts": ["tool_create_line_chart", "tool_create_bar_chart"]
        }
    elif industry == "business":
        return {
            "primary_chart": "tool_create_bar_chart",  # KPI dashboards
            "secondary_charts": ["tool_create_line_chart"]  # Trend analysis
        }
    elif industry == "support":
        return {
            "primary_chart": "tool_create_bar_chart",  # Issue tracking
            "secondary_charts": []
        }
```

#### 3. Communication Tools

**Notification System**:

```python
# Client-specific notification configuration
async def tool_send_notification(title: str, contents: str) -> str:
    # Uses client-specific OneSignal configuration
    notification = Notification(
        app_id=client_onesignal_app_id,
        include_external_user_ids=[client_user_id],
        contents={"en": contents},
        headings={"en": title},
        data={"type": "chat", "client": client_name}
    )
```

**Interactive Tools**:

```python
# Customizable user interaction
def tool_ask_multiple_choice(question: str, choices: list[dict]) -> MultipleChoiceWidget:
    # Can be styled per client brand
    return MultipleChoiceWidget(
        question=question,
        choices=parsed_choices,
        style=client_branding_config
    )
```

## Client Configuration Examples

### 1. Healthcare Client (Hospital/Clinic)

```python
class HospitalAgent(BaseAgent[HealthcareAgentConfig]):
    def get_tools(self) -> dict[str, Callable]:
        # Medical-specific tool configuration
        tools = {
            # Patient data access (HIPAA compliant)
            "tool_search_medical_documents": self.create_medical_search_tool(),
            "tool_get_patient_chart": self.create_patient_chart_tool(),

            # Medical visualization
            "tool_create_zlm_chart": tool_create_zlm_chart,
            "tool_create_vital_signs_chart": self.create_vitals_chart_tool(),

            # Clinical workflow
            "tool_schedule_appointment": self.create_appointment_tool(),
            "tool_send_patient_notification": self.create_patient_notification_tool(),

            # Compliance and safety
            "tool_check_drug_interactions": self.create_drug_check_tool(),
            "tool_validate_treatment_protocol": self.create_protocol_tool(),
        }
        return tools

    # Super agent for medical monitoring
    @staticmethod
    def super_agent_config():
        return SuperAgentConfig(
            interval_seconds=3600,  # Hourly checks for critical patients
            agent_config=HealthcareAgentConfig(),
        )
```

### 2. E-commerce Client

```python
class EcommerceAgent(BaseAgent[EcommerceAgentConfig]):
    def get_tools(self) -> dict[str, Callable]:
        tools = {
            # Order management
            "tool_search_orders": self.create_order_search_tool(),
            "tool_update_order_status": self.create_order_update_tool(),
            "tool_process_refund": self.create_refund_tool(),

            # Customer insights
            "tool_create_sales_chart": tool_create_bar_chart,
            "tool_create_trends_chart": tool_create_line_chart,
            "tool_analyze_customer_behavior": self.create_behavior_analysis_tool(),

            # Marketing automation
            "tool_send_promotional_notification": self.create_promo_notification_tool(),
            "tool_recommend_products": self.create_recommendation_tool(),

            # Inventory management
            "tool_check_inventory": self.create_inventory_tool(),
            "tool_reorder_alert": self.create_reorder_tool(),
        }
        return tools

    @staticmethod
    def super_agent_config():
        return SuperAgentConfig(
            interval_seconds=1800,  # 30 minutes for inventory/sales monitoring
            agent_config=EcommerceAgentConfig(),
        )
```

### 3. Financial Services Client

```python
class FinancialAgent(BaseAgent[FinancialAgentConfig]):
    def get_tools(self) -> dict[str, Callable]:
        tools = {
            # Account management
            "tool_search_accounts": self.create_account_search_tool(),
            "tool_get_account_balance": self.create_balance_tool(),
            "tool_get_transaction_history": self.create_transaction_tool(),

            # Risk analysis
            "tool_create_risk_chart": tool_create_bar_chart,
            "tool_analyze_portfolio": self.create_portfolio_analysis_tool(),
            "tool_check_compliance": self.create_compliance_tool(),

            # Alerts and notifications
            "tool_send_fraud_alert": self.create_fraud_alert_tool(),
            "tool_send_payment_reminder": self.create_payment_reminder_tool(),

            # Reporting
            "tool_generate_monthly_report": self.create_monthly_report_tool(),
            "tool_create_performance_chart": tool_create_line_chart,
        }
        return tools

    @staticmethod
    def super_agent_config():
        return SuperAgentConfig(
            interval_seconds=300,  # 5 minutes for fraud detection
            agent_config=FinancialAgentConfig(),
        )
```

## Advanced Configuration Patterns

### 1. Multi-Tenant Configuration

```python
class MultiTenantAgentConfig(BaseModel):
    tenant_id: str
    tenant_name: str
    roles: list[RoleConfig]

    # Tenant-specific settings
    database_config: dict[str, str]
    api_endpoints: dict[str, str]
    branding_config: dict[str, Any]
    feature_flags: dict[str, bool]

class MultiTenantAgent(BaseAgent[MultiTenantAgentConfig]):
    def __init__(self, config: MultiTenantAgentConfig, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(config)

    def get_tools(self) -> dict[str, Callable]:
        # Load tenant-specific tools
        tools = self.load_tenant_tools(self.tenant_id)

        # Apply tenant-specific configurations
        for tool_name, tool in tools.items():
            if hasattr(tool, 'configure_for_tenant'):
                tool.configure_for_tenant(self.config.tenant_id)

        return tools
```

### 2. Environment-Based Configuration

```python
class EnvironmentConfig:
    @staticmethod
    def get_config(environment: str, client: str) -> BaseModel:
        if environment == "development":
            return DevelopmentAgentConfig(
                roles=[DevelopmentRole()],
                debug_mode=True,
                model_override="openai/gpt-4.1-mini",  # Cost-effective
                log_level="DEBUG"
            )
        elif environment == "staging":
            return StagingAgentConfig(
                roles=[StagingRole()],
                model_override="openai/gpt-4.1",
                log_level="INFO"
            )
        elif environment == "production":
            return ProductionAgentConfig(
                roles=[ProductionRole()],
                model_override="anthropic/claude-sonnet-4",  # High quality
                log_level="WARNING"
            )
```

### 3. Feature Flag Configuration

```python
class FeatureConfig(BaseModel):
    enable_super_agent: bool = True
    enable_notifications: bool = True
    enable_charts: bool = True
    enable_sql_tools: bool = False  # Disabled by default for security
    enable_file_upload: bool = False
    enable_external_apis: bool = True

    # Client-specific features
    custom_tools: list[str] = []
    restricted_tools: list[str] = []

class ConfigurableAgent(BaseAgent):
    def get_tools(self) -> dict[str, Callable]:
        base_tools = super().get_tools()
        feature_config = self.config.feature_config

        # Filter tools based on feature flags
        filtered_tools = {}
        for name, tool in base_tools.items():
            if self.is_tool_enabled(name, feature_config):
                filtered_tools[name] = tool

        # Add custom tools
        for custom_tool_name in feature_config.custom_tools:
            custom_tool = self.load_custom_tool(custom_tool_name)
            if custom_tool:
                filtered_tools[custom_tool_name] = custom_tool

        return filtered_tools
```

## Client Onboarding Workflow

### 1. Initial Client Setup

```python
class ClientOnboardingService:
    async def setup_new_client(
        self,
        client_name: str,
        industry: str,
        requirements: dict[str, Any]
    ) -> ClientAgentConfig:

        # 1. Generate base configuration
        base_config = self.generate_base_config(industry)

        # 2. Customize for client requirements
        customized_config = self.customize_config(base_config, requirements)

        # 3. Setup client-specific resources
        await self.setup_database_access(client_name, customized_config)
        await self.setup_api_endpoints(client_name, customized_config)
        await self.setup_notification_service(client_name, customized_config)

        # 4. Deploy agent instance
        agent_instance = await self.deploy_agent(customized_config)

        return customized_config
```

### 2. Configuration Templates

```python
INDUSTRY_TEMPLATES = {
    "healthcare": {
        "default_model": "anthropic/claude-sonnet-4",
        "required_tools": ["search_documents", "create_zlm_chart", "send_notification"],
        "restricted_tools": ["easylog_sql"],  # HIPAA compliance
        "super_agent_interval": 3600,  # 1 hour
        "default_subjects": ["Medical", "Patient_Care", "Compliance"]
    },
    "finance": {
        "default_model": "anthropic/claude-sonnet-4",
        "required_tools": ["search_documents", "create_bar_chart", "send_notification"],
        "restricted_tools": [],
        "super_agent_interval": 300,  # 5 minutes for fraud detection
        "default_subjects": ["Finance", "Risk", "Compliance"]
    },
    "retail": {
        "default_model": "openai/gpt-4.1",
        "required_tools": ["search_documents", "create_charts", "ask_multiple_choice"],
        "restricted_tools": ["easylog_sql"],
        "super_agent_interval": 1800,  # 30 minutes
        "default_subjects": ["Products", "Orders", "Customer_Service"]
    },
    "education": {
        "default_model": "openai/gpt-4.1-mini",
        "required_tools": ["search_documents", "create_charts", "send_notification"],
        "restricted_tools": [],
        "super_agent_interval": 7200,  # 2 hours
        "default_subjects": ["Curriculum", "Student_Support", "Administration"]
    }
}
```

## Security and Compliance Considerations

### 1. Data Access Control

```python
class SecurityConfig(BaseModel):
    # Role-based access control
    role_permissions: dict[str, list[str]]

    # Data classification
    data_classification_levels: list[str] = ["public", "internal", "confidential", "restricted"]

    # Tool access restrictions
    restricted_tools_by_role: dict[str, list[str]]

    # Audit requirements
    audit_all_actions: bool = True
    log_sensitive_operations: bool = True

    # Compliance frameworks
    compliance_frameworks: list[str] = []  # e.g., ["HIPAA", "GDPR", "SOX"]

class SecureAgent(BaseAgent):
    def validate_tool_access(self, tool_name: str, user_role: str) -> bool:
        security_config = self.config.security_config

        # Check if tool is restricted for this role
        restricted_tools = security_config.restricted_tools_by_role.get(user_role, [])
        if tool_name in restricted_tools:
            self.logger.warning(f"Tool {tool_name} restricted for role {user_role}")
            return False

        return True
```

### 2. Compliance Frameworks

```python
class ComplianceManager:
    @staticmethod
    def get_compliance_config(framework: str) -> dict[str, Any]:
        frameworks = {
            "HIPAA": {
                "restricted_tools": ["easylog_sql", "download_image"],
                "required_audit": True,
                "encryption_required": True,
                "data_retention_days": 2190,  # 6 years
                "allowed_models": ["anthropic/claude-sonnet-4"]  # High security
            },
            "GDPR": {
                "restricted_tools": [],
                "required_audit": True,
                "right_to_deletion": True,
                "data_retention_days": 1095,  # 3 years
                "consent_tracking": True
            },
            "SOX": {
                "restricted_tools": [],
                "required_audit": True,
                "financial_controls": True,
                "segregation_of_duties": True
            }
        }
        return frameworks.get(framework, {})
```

## Performance and Scaling Considerations

### 1. Model Selection Strategy

```python
class ModelSelectionStrategy:
    @staticmethod
    def select_model(
        use_case: str,
        volume: str,
        budget: str,
        quality_requirement: str
    ) -> str:

        if quality_requirement == "premium":
            return "anthropic/claude-sonnet-4"

        if volume == "high" and budget == "low":
            return "openai/gpt-4.1-nano"

        if use_case in ["customer_service", "support"]:
            return "openai/gpt-4.1-mini"

        if use_case in ["data_analysis", "reporting"]:
            return "openai/gpt-4.1"

        # Default balanced option
        return "openai/gpt-4.1-mini"
```

### 2. Caching and Optimization

```python
class PerformanceConfig(BaseModel):
    enable_response_caching: bool = True
    cache_duration_seconds: int = 3600

    enable_tool_result_caching: bool = True
    tool_cache_duration_seconds: int = 300

    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30

    enable_preprocessing: bool = True
    enable_response_streaming: bool = True
```

## Best Practices for Client Implementation

### 1. Configuration Management

```python
class ClientConfigManager:
    def __init__(self, config_storage: str = "database"):
        self.storage = config_storage

    async def load_client_config(self, client_id: str) -> ClientAgentConfig:
        # Load from secure storage
        config_data = await self.fetch_config(client_id)
        return ClientAgentConfig(**config_data)

    async def update_client_config(
        self,
        client_id: str,
        updates: dict[str, Any]
    ) -> bool:
        # Version control for config changes
        current_config = await self.load_client_config(client_id)
        new_version = self.create_version(current_config, updates)
        return await self.save_config(client_id, new_version)
```

### 2. Testing and Validation

```python
class ClientConfigValidator:
    def validate_config(self, config: ClientAgentConfig) -> list[str]:
        errors = []

        # Validate roles
        for role in config.roles:
            if not self.validate_model_exists(role.model):
                errors.append(f"Invalid model: {role.model}")

            if not self.validate_tools_regex(role.tools_regex):
                errors.append(f"Invalid tools regex: {role.tools_regex}")

        # Validate security requirements
        if not self.validate_security_compliance(config):
            errors.append("Security compliance validation failed")

        return errors
```

### 3. Monitoring and Analytics

```python
class ClientUsageMonitor:
    async def track_usage(
        self,
        client_id: str,
        agent_type: str,
        tool_used: str,
        tokens_used: int,
        cost: float
    ):
        # Track for billing and optimization
        usage_record = {
            "timestamp": datetime.now(),
            "client_id": client_id,
            "agent_type": agent_type,
            "tool_used": tool_used,
            "tokens_used": tokens_used,
            "cost": cost
        }
        await self.store_usage_record(usage_record)

    async def generate_client_report(self, client_id: str) -> dict[str, Any]:
        # Generate usage and performance reports
        return {
            "total_interactions": await self.get_interaction_count(client_id),
            "cost_breakdown": await self.get_cost_breakdown(client_id),
            "tool_usage_stats": await self.get_tool_stats(client_id),
            "performance_metrics": await self.get_performance_metrics(client_id)
        }
```

This comprehensive guide provides the foundation for building flexible, client-specific AI solutions using the agent framework, with clear examples for different industries and use cases.
