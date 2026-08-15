from common.utils.env import get_env, get_env_int

JOB_SCORING_TASK_GROUP = 'job_scoring_batch'
SCORE_THRESHOLD = get_env_int('SCORE_THRESHOLD')
JOB_SCORING_CLAUDE_MODEL = get_env('JOB_SCORING_CLAUDE_MODEL')
