export const JOB_STATUS_OPTIONS = [
  'To Apply',
  'Applied',
  'In Progress',
  'Rejected',
  'Not considering',
  'Other',
  'Pending',
] as const

export const JOB_REFERRAL_STATUS_OPTIONS = [
  'Not asking',
  'Referral required',
  'Referral asked',
  'Referral got',
  'Other',
] as const

export const DEFAULT_JOB_STATUS = JOB_STATUS_OPTIONS[0]
export const DEFAULT_JOB_REFERRAL_STATUS = JOB_REFERRAL_STATUS_OPTIONS[0]
