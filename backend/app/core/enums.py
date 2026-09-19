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
