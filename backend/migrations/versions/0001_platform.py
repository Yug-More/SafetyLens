"""Adopt historical schema and add platform tables without dropping data.

Revision ID: 0001_platform
Downgrade is intentionally refused to avoid removing historical evidence.
"""
from alembic import op
import sqlalchemy as sa
revision = '0001_platform'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    if not sa.inspect(op.get_bind()).has_table('cameras'):
        op.create_table('cameras',
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('stream_status', sa.String(length=64), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cameras')),
        sa.UniqueConstraint('name', name=op.f('uq_cameras_name'))
        )
    if 'ix_cameras_location' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('cameras')}:
        op.create_index(op.f('ix_cameras_location'), 'cameras', ['location'], unique=False)
    if 'ix_cameras_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('cameras')}:
        op.create_index(op.f('ix_cameras_status'), 'cameras', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('login_throttles'):
        op.create_table('login_throttles',
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key', name=op.f('pk_login_throttles'))
        )
    if not sa.inspect(op.get_bind()).has_table('platform_users'):
        op.create_table('platform_users',
        sa.Column('username', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_platform_users'))
        )
    if 'ix_platform_users_username' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('platform_users')}:
        op.create_index(op.f('ix_platform_users_username'), 'platform_users', ['username'], unique=True)
    if not sa.inspect(op.get_bind()).has_table('safety_procedures'):
        op.create_table('safety_procedures',
        sa.Column('procedure_code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=120), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('source_filename', sa.String(length=255), nullable=True),
        sa.Column('source_format', sa.String(length=32), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('stored_filename', sa.String(length=255), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('is_sample', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_safety_procedures'))
        )
    if 'ix_safety_procedures_category' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('safety_procedures')}:
        op.create_index(op.f('ix_safety_procedures_category'), 'safety_procedures', ['category'], unique=False)
    if 'ix_safety_procedures_content_hash' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('safety_procedures')}:
        op.create_index(op.f('ix_safety_procedures_content_hash'), 'safety_procedures', ['content_hash'], unique=False)
    if 'ix_safety_procedures_is_active' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('safety_procedures')}:
        op.create_index(op.f('ix_safety_procedures_is_active'), 'safety_procedures', ['is_active'], unique=False)
    if 'ix_safety_procedures_procedure_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('safety_procedures')}:
        op.create_index(op.f('ix_safety_procedures_procedure_code'), 'safety_procedures', ['procedure_code'], unique=True)
    if not sa.inspect(op.get_bind()).has_table('stream_events'):
        op.create_table('stream_events',
        sa.Column('sequence', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('kind', sa.String(length=80), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('sequence', name=op.f('pk_stream_events')),
        sqlite_autoincrement=True
        )
    if not sa.inspect(op.get_bind()).has_table('system_services'):
        op.create_table('system_services',
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_system_services')),
        sa.UniqueConstraint('name', name=op.f('uq_system_services_name'))
        )
    if not sa.inspect(op.get_bind()).has_table('camera_configurations'):
        op.create_table('camera_configurations',
        sa.Column('camera_id', sa.String(length=36), nullable=False),
        sa.Column('facility', sa.String(length=120), nullable=False),
        sa.Column('zone', sa.String(length=120), nullable=False),
        sa.Column('source_kind', sa.String(length=20), nullable=False),
        sa.Column('source_ciphertext', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('policy_json', sa.Text(), nullable=False),
        sa.Column('health_details', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name=op.f('fk_camera_configurations_camera_id_cameras')),
        sa.PrimaryKeyConstraint('camera_id', name=op.f('pk_camera_configurations'))
        )
    if not sa.inspect(op.get_bind()).has_table('camera_ppe_policies'):
        op.create_table('camera_ppe_policies',
        sa.Column('camera_id', sa.String(length=36), nullable=False),
        sa.Column('zone_label', sa.String(length=200), nullable=False),
        sa.Column('required_ppe_json', sa.Text(), nullable=False),
        sa.Column('procedure_code', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name=op.f('fk_camera_ppe_policies_camera_id_cameras')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_camera_ppe_policies')),
        sa.UniqueConstraint('camera_id', name='uq_camera_ppe_policies_camera')
        )
    if 'ix_camera_ppe_policies_camera_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('camera_ppe_policies')}:
        op.create_index(op.f('ix_camera_ppe_policies_camera_id'), 'camera_ppe_policies', ['camera_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('incidents'):
        op.create_table('incidents',
        sa.Column('incident_code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('incident_type', sa.String(length=64), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('camera_id', sa.String(length=36), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('review_status', sa.String(length=32), nullable=False),
        sa.Column('matched_procedure_id', sa.String(length=36), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name=op.f('fk_incidents_camera_id_cameras')),
        sa.ForeignKeyConstraint(['matched_procedure_id'], ['safety_procedures.id'], name=op.f('fk_incidents_matched_procedure_id_safety_procedures')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_incidents'))
        )
    if 'ix_incidents_camera_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_camera_id'), 'incidents', ['camera_id'], unique=False)
    if 'ix_incidents_detected_at' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_detected_at'), 'incidents', ['detected_at'], unique=False)
    if 'ix_incidents_incident_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_incident_code'), 'incidents', ['incident_code'], unique=True)
    if 'ix_incidents_incident_type' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_incident_type'), 'incidents', ['incident_type'], unique=False)
    if 'ix_incidents_severity' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_severity'), 'incidents', ['severity'], unique=False)
    if 'ix_incidents_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incidents')}:
        op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('platform_sessions'):
        op.create_table('platform_sessions',
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('csrf_token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['platform_users.id'], name=op.f('fk_platform_sessions_user_id_platform_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_platform_sessions'))
        )
    if 'ix_platform_sessions_expires_at' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('platform_sessions')}:
        op.create_index(op.f('ix_platform_sessions_expires_at'), 'platform_sessions', ['expires_at'], unique=False)
    if 'ix_platform_sessions_token_hash' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('platform_sessions')}:
        op.create_index(op.f('ix_platform_sessions_token_hash'), 'platform_sessions', ['token_hash'], unique=True)
    if 'ix_platform_sessions_user_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('platform_sessions')}:
        op.create_index(op.f('ix_platform_sessions_user_id'), 'platform_sessions', ['user_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('procedure_chunks'):
        op.create_table('procedure_chunks',
        sa.Column('procedure_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_code', sa.String(length=64), nullable=False),
        sa.Column('chunk_order', sa.Integer(), nullable=False),
        sa.Column('section_heading', sa.String(length=300), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['procedure_id'], ['safety_procedures.id'], name=op.f('fk_procedure_chunks_procedure_id_safety_procedures')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_procedure_chunks')),
        sa.UniqueConstraint('procedure_id', 'chunk_order', name='uq_procedure_chunk_order')
        )
    if 'ix_procedure_chunks_chunk_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_chunks')}:
        op.create_index(op.f('ix_procedure_chunks_chunk_code'), 'procedure_chunks', ['chunk_code'], unique=True)
    if 'ix_procedure_chunks_procedure_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_chunks')}:
        op.create_index(op.f('ix_procedure_chunks_procedure_id'), 'procedure_chunks', ['procedure_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('video_assets'):
        op.create_table('video_assets',
        sa.Column('asset_code', sa.String(length=64), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=120), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('frame_count', sa.Integer(), nullable=True),
        sa.Column('camera_id', sa.String(length=36), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('demo_scenario', sa.String(length=64), nullable=True),
        sa.Column('demo_ppe_observation', sa.String(length=80), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name=op.f('fk_video_assets_camera_id_cameras')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_video_assets')),
        sa.UniqueConstraint('stored_filename', name=op.f('uq_video_assets_stored_filename'))
        )
    if 'ix_video_assets_asset_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('video_assets')}:
        op.create_index(op.f('ix_video_assets_asset_code'), 'video_assets', ['asset_code'], unique=True)
    if 'ix_video_assets_camera_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('video_assets')}:
        op.create_index(op.f('ix_video_assets_camera_id'), 'video_assets', ['camera_id'], unique=False)
    if 'ix_video_assets_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('video_assets')}:
        op.create_index(op.f('ix_video_assets_status'), 'video_assets', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('activity_events'):
        op.create_table('activity_events',
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_activity_events_incident_id_incidents')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_events'))
        )
    if 'ix_activity_events_event_type' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('activity_events')}:
        op.create_index(op.f('ix_activity_events_event_type'), 'activity_events', ['event_type'], unique=False)
    if 'ix_activity_events_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('activity_events')}:
        op.create_index(op.f('ix_activity_events_incident_id'), 'activity_events', ['incident_id'], unique=False)
    if 'ix_activity_events_occurred_at' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('activity_events')}:
        op.create_index(op.f('ix_activity_events_occurred_at'), 'activity_events', ['occurred_at'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('evidence'):
        op.create_table('evidence',
        sa.Column('incident_id', sa.String(length=36), nullable=False),
        sa.Column('evidence_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('timestamp_seconds', sa.Float(), nullable=False),
        sa.Column('media_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_evidence_incident_id_incidents')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_evidence'))
        )
    if 'ix_evidence_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('evidence')}:
        op.create_index(op.f('ix_evidence_incident_id'), 'evidence', ['incident_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('incident_operations'):
        op.create_table('incident_operations',
        sa.Column('incident_id', sa.String(length=36), nullable=False),
        sa.Column('assigned_user_id', sa.String(length=36), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['platform_users.id'], name=op.f('fk_incident_operations_assigned_user_id_platform_users')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_incident_operations_incident_id_incidents')),
        sa.PrimaryKeyConstraint('incident_id', name=op.f('pk_incident_operations'))
        )
    if not sa.inspect(op.get_bind()).has_table('processing_jobs'):
        op.create_table('processing_jobs',
        sa.Column('job_code', sa.String(length=64), nullable=False),
        sa.Column('video_asset_id', sa.String(length=36), nullable=False),
        sa.Column('job_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(length=120), nullable=False),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], name=op.f('fk_processing_jobs_video_asset_id_video_assets')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_processing_jobs'))
        )
    if 'ix_processing_jobs_job_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('processing_jobs')}:
        op.create_index(op.f('ix_processing_jobs_job_code'), 'processing_jobs', ['job_code'], unique=True)
    if 'ix_processing_jobs_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('processing_jobs')}:
        op.create_index(op.f('ix_processing_jobs_status'), 'processing_jobs', ['status'], unique=False)
    if 'ix_processing_jobs_video_asset_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('processing_jobs')}:
        op.create_index(op.f('ix_processing_jobs_video_asset_id'), 'processing_jobs', ['video_asset_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('recommended_actions'):
        op.create_table('recommended_actions',
        sa.Column('incident_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_recommended_actions_incident_id_incidents')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_recommended_actions'))
        )
    if 'ix_recommended_actions_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('recommended_actions')}:
        op.create_index(op.f('ix_recommended_actions_incident_id'), 'recommended_actions', ['incident_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('video_frames'):
        op.create_table('video_frames',
        sa.Column('video_asset_id', sa.String(length=36), nullable=False),
        sa.Column('frame_code', sa.String(length=64), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp_seconds', sa.Float(), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], name=op.f('fk_video_frames_video_asset_id_video_assets')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_video_frames')),
        sa.UniqueConstraint('stored_filename', name=op.f('uq_video_frames_stored_filename'))
        )
    if 'ix_video_frames_frame_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('video_frames')}:
        op.create_index(op.f('ix_video_frames_frame_code'), 'video_frames', ['frame_code'], unique=True)
    if 'ix_video_frames_video_asset_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('video_frames')}:
        op.create_index(op.f('ix_video_frames_video_asset_id'), 'video_frames', ['video_asset_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('incident_analyses'):
        op.create_table('incident_analyses',
        sa.Column('analysis_code', sa.String(length=64), nullable=False),
        sa.Column('video_asset_id', sa.String(length=36), nullable=False),
        sa.Column('processing_job_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('is_simulated', sa.Boolean(), nullable=False),
        sa.Column('incident_detected', sa.Boolean(), nullable=True),
        sa.Column('incident_type', sa.String(length=120), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('detailed_analysis', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=32), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('recommended_actions_json', sa.Text(), nullable=True),
        sa.Column('limitations_json', sa.Text(), nullable=True),
        sa.Column('inconclusive', sa.Boolean(), nullable=False),
        sa.Column('required_ppe_json', sa.Text(), nullable=True),
        sa.Column('observed_ppe_json', sa.Text(), nullable=True),
        sa.Column('possibly_missing_ppe_json', sa.Text(), nullable=True),
        sa.Column('analysis_mode', sa.String(length=64), nullable=True),
        sa.Column('human_review_required', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['processing_job_id'], ['processing_jobs.id'], name=op.f('fk_incident_analyses_processing_job_id_processing_jobs')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], name=op.f('fk_incident_analyses_video_asset_id_video_assets')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_incident_analyses'))
        )
    if 'ix_incident_analyses_analysis_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_analyses')}:
        op.create_index(op.f('ix_incident_analyses_analysis_code'), 'incident_analyses', ['analysis_code'], unique=True)
    if 'ix_incident_analyses_processing_job_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_analyses')}:
        op.create_index(op.f('ix_incident_analyses_processing_job_id'), 'incident_analyses', ['processing_job_id'], unique=False)
    if 'ix_incident_analyses_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_analyses')}:
        op.create_index(op.f('ix_incident_analyses_status'), 'incident_analyses', ['status'], unique=False)
    if 'ix_incident_analyses_video_asset_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_analyses')}:
        op.create_index(op.f('ix_incident_analyses_video_asset_id'), 'incident_analyses', ['video_asset_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('analysis_evidence'):
        op.create_table('analysis_evidence',
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('frame_id', sa.String(length=36), nullable=False),
        sa.Column('frame_code', sa.String(length=64), nullable=False),
        sa.Column('timestamp_seconds', sa.Float(), nullable=False),
        sa.Column('observation', sa.Text(), nullable=False),
        sa.Column('relevance', sa.String(length=32), nullable=False),
        sa.Column('content_url', sa.String(length=500), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_analysis_evidence_analysis_id_incident_analyses')),
        sa.ForeignKeyConstraint(['frame_id'], ['video_frames.id'], name=op.f('fk_analysis_evidence_frame_id_video_frames')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_evidence'))
        )
    if 'ix_analysis_evidence_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('analysis_evidence')}:
        op.create_index(op.f('ix_analysis_evidence_analysis_id'), 'analysis_evidence', ['analysis_id'], unique=False)
    if 'ix_analysis_evidence_frame_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('analysis_evidence')}:
        op.create_index(op.f('ix_analysis_evidence_frame_code'), 'analysis_evidence', ['frame_code'], unique=False)
    if 'ix_analysis_evidence_frame_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('analysis_evidence')}:
        op.create_index(op.f('ix_analysis_evidence_frame_id'), 'analysis_evidence', ['frame_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('analysis_reviews'):
        op.create_table('analysis_reviews',
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('reviewer_name', sa.String(length=120), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_analysis_reviews_analysis_id_incident_analyses')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_reviews'))
        )
    if 'ix_analysis_reviews_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('analysis_reviews')}:
        op.create_index(op.f('ix_analysis_reviews_analysis_id'), 'analysis_reviews', ['analysis_id'], unique=True)
    if not sa.inspect(op.get_bind()).has_table('detector_event_ingestions'):
        op.create_table('detector_event_ingestions',
        sa.Column('event_id', sa.String(length=120), nullable=False),
        sa.Column('schema_version', sa.String(length=20), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('source_id', sa.String(length=120), nullable=False),
        sa.Column('camera_id', sa.String(length=36), nullable=True),
        sa.Column('track_id', sa.String(length=120), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('clip_event_offset_seconds', sa.Float(), nullable=True),
        sa.Column('detector_state', sa.String(length=40), nullable=True),
        sa.Column('trigger_signals_json', sa.Text(), nullable=False),
        sa.Column('pose_quality', sa.Float(), nullable=True),
        sa.Column('heuristic_score', sa.Float(), nullable=True),
        sa.Column('metrics_json', sa.Text(), nullable=False),
        sa.Column('limitations_json', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('video_asset_id', sa.String(length=36), nullable=True),
        sa.Column('processing_job_id', sa.String(length=36), nullable=True),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('error_code', sa.String(length=80), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('is_simulated', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_detector_event_ingestions_analysis_id_incident_analyses')),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], name=op.f('fk_detector_event_ingestions_camera_id_cameras')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_detector_event_ingestions_incident_id_incidents')),
        sa.ForeignKeyConstraint(['processing_job_id'], ['processing_jobs.id'], name=op.f('fk_detector_event_ingestions_processing_job_id_processing_jobs')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], name=op.f('fk_detector_event_ingestions_video_asset_id_video_assets')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_detector_event_ingestions')),
        sa.UniqueConstraint('event_id', name='uq_detector_event_ingestions_event_id')
        )
    if 'ix_detector_event_ingestions_event_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('detector_event_ingestions')}:
        op.create_index(op.f('ix_detector_event_ingestions_event_id'), 'detector_event_ingestions', ['event_id'], unique=False)
    if 'ix_detector_event_ingestions_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('detector_event_ingestions')}:
        op.create_index(op.f('ix_detector_event_ingestions_status'), 'detector_event_ingestions', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('operator_notifications'):
        op.create_table('operator_notifications',
        sa.Column('notification_code', sa.String(length=64), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('video_asset_id', sa.String(length=36), nullable=True),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('incident_type', sa.String(length=80), nullable=True),
        sa.Column('camera_id', sa.String(length=36), nullable=True),
        sa.Column('camera_name', sa.String(length=120), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('review_status', sa.String(length=32), nullable=False),
        sa.Column('dismissed', sa.Boolean(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_operator_notifications_analysis_id_incident_analyses')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_operator_notifications_incident_id_incidents')),
        sa.ForeignKeyConstraint(['video_asset_id'], ['video_assets.id'], name=op.f('fk_operator_notifications_video_asset_id_video_assets')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_operator_notifications')),
        sa.UniqueConstraint('analysis_id', name='uq_operator_notifications_analysis')
        )
    if 'ix_operator_notifications_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('operator_notifications')}:
        op.create_index(op.f('ix_operator_notifications_analysis_id'), 'operator_notifications', ['analysis_id'], unique=False)
    if 'ix_operator_notifications_notification_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('operator_notifications')}:
        op.create_index(op.f('ix_operator_notifications_notification_code'), 'operator_notifications', ['notification_code'], unique=True)
    if 'ix_operator_notifications_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('operator_notifications')}:
        op.create_index(op.f('ix_operator_notifications_status'), 'operator_notifications', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('procedure_retrievals'):
        op.create_table('procedure_retrievals',
        sa.Column('retrieval_code', sa.String(length=64), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('method', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('match_count', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_procedure_retrievals_analysis_id_incident_analyses')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_procedure_retrievals'))
        )
    if 'ix_procedure_retrievals_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_retrievals')}:
        op.create_index(op.f('ix_procedure_retrievals_analysis_id'), 'procedure_retrievals', ['analysis_id'], unique=False)
    if 'ix_procedure_retrievals_retrieval_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_retrievals')}:
        op.create_index(op.f('ix_procedure_retrievals_retrieval_code'), 'procedure_retrievals', ['retrieval_code'], unique=True)
    if 'ix_procedure_retrievals_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_retrievals')}:
        op.create_index(op.f('ix_procedure_retrievals_status'), 'procedure_retrievals', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('procedure_retrieval_matches'):
        op.create_table('procedure_retrieval_matches',
        sa.Column('retrieval_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('method', sa.String(length=32), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['procedure_chunks.id'], name=op.f('fk_procedure_retrieval_matches_chunk_id_procedure_chunks')),
        sa.ForeignKeyConstraint(['retrieval_id'], ['procedure_retrievals.id'], name=op.f('fk_procedure_retrieval_matches_retrieval_id_procedure_retrievals')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_procedure_retrieval_matches'))
        )
    if 'ix_procedure_retrieval_matches_chunk_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_retrieval_matches')}:
        op.create_index(op.f('ix_procedure_retrieval_matches_chunk_id'), 'procedure_retrieval_matches', ['chunk_id'], unique=False)
    if 'ix_procedure_retrieval_matches_retrieval_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('procedure_retrieval_matches')}:
        op.create_index(op.f('ix_procedure_retrieval_matches_retrieval_id'), 'procedure_retrieval_matches', ['retrieval_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('response_plans'):
        op.create_table('response_plans',
        sa.Column('plan_code', sa.String(length=64), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('retrieval_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('provider_model', sa.String(length=120), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('is_simulated', sa.Boolean(), nullable=False),
        sa.Column('limitations_json', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('approval_status', sa.String(length=32), nullable=False),
        sa.Column('execution_status', sa.String(length=32), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_response_plans_analysis_id_incident_analyses')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_response_plans_incident_id_incidents')),
        sa.ForeignKeyConstraint(['retrieval_id'], ['procedure_retrievals.id'], name=op.f('fk_response_plans_retrieval_id_procedure_retrievals')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_response_plans'))
        )
    if 'ix_response_plans_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_analysis_id'), 'response_plans', ['analysis_id'], unique=False)
    if 'ix_response_plans_approval_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_approval_status'), 'response_plans', ['approval_status'], unique=False)
    if 'ix_response_plans_execution_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_execution_status'), 'response_plans', ['execution_status'], unique=False)
    if 'ix_response_plans_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_incident_id'), 'response_plans', ['incident_id'], unique=False)
    if 'ix_response_plans_plan_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_plan_code'), 'response_plans', ['plan_code'], unique=True)
    if 'ix_response_plans_retrieval_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_retrieval_id'), 'response_plans', ['retrieval_id'], unique=False)
    if 'ix_response_plans_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('response_plans')}:
        op.create_index(op.f('ix_response_plans_status'), 'response_plans', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('plan_approvals'):
        op.create_table('plan_approvals',
        sa.Column('approval_code', sa.String(length=64), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reviewer_name', sa.String(length=120), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('selected_action_ids_json', sa.Text(), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_simulated', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_plan_approvals_incident_id_incidents')),
        sa.ForeignKeyConstraint(['plan_id'], ['response_plans.id'], name=op.f('fk_plan_approvals_plan_id_response_plans')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_plan_approvals'))
        )
    if 'ix_plan_approvals_approval_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_approvals')}:
        op.create_index(op.f('ix_plan_approvals_approval_code'), 'plan_approvals', ['approval_code'], unique=True)
    if 'ix_plan_approvals_correlation_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_approvals')}:
        op.create_index(op.f('ix_plan_approvals_correlation_id'), 'plan_approvals', ['correlation_id'], unique=False)
    if 'ix_plan_approvals_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_approvals')}:
        op.create_index(op.f('ix_plan_approvals_incident_id'), 'plan_approvals', ['incident_id'], unique=False)
    if 'ix_plan_approvals_plan_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_approvals')}:
        op.create_index(op.f('ix_plan_approvals_plan_id'), 'plan_approvals', ['plan_id'], unique=False)
    if 'ix_plan_approvals_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_approvals')}:
        op.create_index(op.f('ix_plan_approvals_status'), 'plan_approvals', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('planned_actions'):
        op.create_table('planned_actions',
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('action_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('responsible_role', sa.String(length=120), nullable=False),
        sa.Column('requires_human_approval', sa.Boolean(), nullable=False),
        sa.Column('is_policy_grounded', sa.Boolean(), nullable=False),
        sa.Column('selection_status', sa.String(length=32), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['response_plans.id'], name=op.f('fk_planned_actions_plan_id_response_plans')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_planned_actions'))
        )
    if 'ix_planned_actions_plan_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('planned_actions')}:
        op.create_index(op.f('ix_planned_actions_plan_id'), 'planned_actions', ['plan_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('action_executions'):
        op.create_table('action_executions',
        sa.Column('execution_code', sa.String(length=64), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('action_id', sa.String(length=36), nullable=False),
        sa.Column('approval_id', sa.String(length=36), nullable=False),
        sa.Column('idempotency_key', sa.String(length=120), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('requested_target', sa.String(length=200), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('simulation', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(length=64), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('external_reference', sa.String(length=120), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['planned_actions.id'], name=op.f('fk_action_executions_action_id_planned_actions')),
        sa.ForeignKeyConstraint(['approval_id'], ['plan_approvals.id'], name=op.f('fk_action_executions_approval_id_plan_approvals')),
        sa.ForeignKeyConstraint(['plan_id'], ['response_plans.id'], name=op.f('fk_action_executions_plan_id_response_plans')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_action_executions')),
        sa.UniqueConstraint('idempotency_key', name='uq_action_execution_idempotency')
        )
    if 'ix_action_executions_action_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_action_id'), 'action_executions', ['action_id'], unique=False)
    if 'ix_action_executions_approval_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_approval_id'), 'action_executions', ['approval_id'], unique=False)
    if 'ix_action_executions_correlation_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_correlation_id'), 'action_executions', ['correlation_id'], unique=False)
    if 'ix_action_executions_execution_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_execution_code'), 'action_executions', ['execution_code'], unique=True)
    if 'ix_action_executions_plan_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_plan_id'), 'action_executions', ['plan_id'], unique=False)
    if 'ix_action_executions_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('action_executions')}:
        op.create_index(op.f('ix_action_executions_status'), 'action_executions', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('incident_reports'):
        op.create_table('incident_reports',
        sa.Column('report_code', sa.String(length=64), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=True),
        sa.Column('approval_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('simulation', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary_json', sa.Text(), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=True),
        sa.Column('content_sha256', sa.String(length=64), nullable=True),
        sa.Column('incomplete_reason', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approval_id'], ['plan_approvals.id'], name=op.f('fk_incident_reports_approval_id_plan_approvals')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_incident_reports_incident_id_incidents')),
        sa.ForeignKeyConstraint(['plan_id'], ['response_plans.id'], name=op.f('fk_incident_reports_plan_id_response_plans')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_incident_reports'))
        )
    if 'ix_incident_reports_approval_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_reports')}:
        op.create_index(op.f('ix_incident_reports_approval_id'), 'incident_reports', ['approval_id'], unique=False)
    if 'ix_incident_reports_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_reports')}:
        op.create_index(op.f('ix_incident_reports_incident_id'), 'incident_reports', ['incident_id'], unique=False)
    if 'ix_incident_reports_plan_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_reports')}:
        op.create_index(op.f('ix_incident_reports_plan_id'), 'incident_reports', ['plan_id'], unique=False)
    if 'ix_incident_reports_report_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_reports')}:
        op.create_index(op.f('ix_incident_reports_report_code'), 'incident_reports', ['report_code'], unique=True)
    if 'ix_incident_reports_status' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('incident_reports')}:
        op.create_index(op.f('ix_incident_reports_status'), 'incident_reports', ['status'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('plan_citations'):
        op.create_table('plan_citations',
        sa.Column('action_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['planned_actions.id'], name=op.f('fk_plan_citations_action_id_planned_actions')),
        sa.ForeignKeyConstraint(['chunk_id'], ['procedure_chunks.id'], name=op.f('fk_plan_citations_chunk_id_procedure_chunks')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_plan_citations'))
        )
    if 'ix_plan_citations_action_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_citations')}:
        op.create_index(op.f('ix_plan_citations_action_id'), 'plan_citations', ['action_id'], unique=False)
    if 'ix_plan_citations_chunk_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('plan_citations')}:
        op.create_index(op.f('ix_plan_citations_chunk_id'), 'plan_citations', ['chunk_id'], unique=False)
    if not sa.inspect(op.get_bind()).has_table('audit_events'):
        op.create_table('audit_events',
        sa.Column('event_code', sa.String(length=64), nullable=False),
        sa.Column('incident_id', sa.String(length=36), nullable=True),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('plan_id', sa.String(length=36), nullable=True),
        sa.Column('execution_id', sa.String(length=36), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('actor_type', sa.String(length=32), nullable=False),
        sa.Column('actor_name', sa.String(length=120), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.String(length=64), nullable=True),
        sa.Column('new_status', sa.String(length=64), nullable=True),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('simulation', sa.Boolean(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['incident_analyses.id'], name=op.f('fk_audit_events_analysis_id_incident_analyses')),
        sa.ForeignKeyConstraint(['execution_id'], ['action_executions.id'], name=op.f('fk_audit_events_execution_id_action_executions')),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], name=op.f('fk_audit_events_incident_id_incidents')),
        sa.ForeignKeyConstraint(['plan_id'], ['response_plans.id'], name=op.f('fk_audit_events_plan_id_response_plans')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_events'))
        )
    if 'ix_audit_events_analysis_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_analysis_id'), 'audit_events', ['analysis_id'], unique=False)
    if 'ix_audit_events_correlation_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_correlation_id'), 'audit_events', ['correlation_id'], unique=False)
    if 'ix_audit_events_event_code' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_event_code'), 'audit_events', ['event_code'], unique=True)
    if 'ix_audit_events_event_type' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_event_type'), 'audit_events', ['event_type'], unique=False)
    if 'ix_audit_events_execution_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_execution_id'), 'audit_events', ['execution_id'], unique=False)
    if 'ix_audit_events_incident_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_incident_id'), 'audit_events', ['incident_id'], unique=False)
    if 'ix_audit_events_occurred_at' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_occurred_at'), 'audit_events', ['occurred_at'], unique=False)
    if 'ix_audit_events_plan_id' not in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes('audit_events')}:
        op.create_index(op.f('ix_audit_events_plan_id'), 'audit_events', ['plan_id'], unique=False)

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled; restore an explicitly reviewed backup instead.')
