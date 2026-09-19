import enum


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"


class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class ServiceStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class ActionPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    STANDARD = "standard"


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    VIDEO_PREPARE = "video_prepare"
    ANALYSIS = "analysis"


class AnalysisStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class AnalysisSeverity(str, enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewDecision(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"


class AIProviderName(str, enum.Enum):
    DEMO = "demo"
    OPENAI = "openai"


class ProcedureSourceFormat(str, enum.Enum):
    TXT = "txt"
    MARKDOWN = "markdown"
    PDF = "pdf"
    SEED = "seed"


class RetrievalMethod(str, enum.Enum):
    LEXICAL = "lexical"
    HYBRID = "hybrid"


class RetrievalStatus(str, enum.Enum):
    COMPLETED = "completed"
    INSUFFICIENT = "insufficient"
    FAILED = "failed"


class ResponsePlanStatus(str, enum.Enum):
    QUEUED = "queued"
    COMPLETED = "completed"
    INSUFFICIENT_POLICY = "insufficient_policy"
    FAILED = "failed"


class PlannerProviderName(str, enum.Enum):
    DEMO = "demo"
    OPENAI = "openai"


class PlanApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"


class PlanExecutionStatus(str, enum.Enum):
    NONE = "none"
    IN_PROGRESS = "in_progress"
    EXECUTED = "executed"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SimulatedActionType(str, enum.Enum):
    ALERT_SUPERVISOR = "alert_supervisor"
    REQUEST_MEDICAL = "request_medical"
    CREATE_TICKET = "create_ticket"
    PRESERVE_EVIDENCE = "preserve_evidence"
    AREA_ISOLATION = "area_isolation"
    FOLLOW_UP_REVIEW = "follow_up_review"
    GENERIC = "generic"


class AuditActorType(str, enum.Enum):
    SYSTEM = "system"
    HUMAN = "human"
    SIMULATOR = "simulator"


class AuditEventType(str, enum.Enum):
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_REVIEWED = "analysis_reviewed"
    RETRIEVAL_COMPLETED = "retrieval_completed"
    PLAN_GENERATED = "plan_generated"
    PLAN_VIEWED = "plan_viewed"
    PLAN_APPROVED = "plan_approved"
    PLAN_PARTIALLY_APPROVED = "plan_partially_approved"
    PLAN_REJECTED = "plan_rejected"
    EXECUTION_REQUESTED = "execution_requested"
    ACTION_STARTED = "action_started"
    ACTION_SUCCEEDED = "action_succeeded"
    ACTION_FAILED = "action_failed"
    RETRY_REQUESTED = "retry_requested"
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"


class ReportStatus(str, enum.Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
