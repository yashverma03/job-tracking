import type { FocusEvent, KeyboardEvent } from 'react'

import dayjs from 'dayjs'
import { Formik, Form, Field, type FieldProps } from 'formik'
import { X } from 'lucide-react'
import * as Yup from 'yup'

import { Dropdown } from '../../../common/components/Dropdown'
import {
  DEFAULT_JOB_REFERRAL_STATUS,
  DEFAULT_JOB_STATUS,
  JOB_REFERRAL_STATUS_OPTIONS,
  JOB_STATUS_OPTIONS,
  REFERRAL_STATUS_DROPDOWN_OPTIONS,
  STATUS_DROPDOWN_OPTIONS,
} from '../constants/job.constants'
import type { JobFormValues, JobUpdateRequest } from '../interfaces/job.interfaces'
import type { Job } from '../types/job.types'
import { cleanJobUrl } from '../utils/urlCleaner'
import styles from './JobFormModal.module.css'

const CREATED_AT_FORMAT = 'DD MMM YYYY'

const jobFormSchema = Yup.object({
  url: Yup.string().trim(),
  secondaryUrl: Yup.string().trim(),
  companyName: Yup.string(),
  title: Yup.string(),
  officialId: Yup.string(),
  description: Yup.string(),
  location: Yup.string(),
  notes: Yup.string(),
  status: Yup.string().oneOf(JOB_STATUS_OPTIONS).required(),
  referralStatus: Yup.string().oneOf(JOB_REFERRAL_STATUS_OPTIONS).required(),
  score: Yup.string().trim().matches(/^-?\d*$/, 'Score must be a whole number'),
  analysis: Yup.string(),
})

function jobToFormValues(job: Job | null): JobFormValues {
  return {
    url: job?.url ?? '',
    secondaryUrl: job?.secondaryUrl ?? '',
    companyName: job?.companyName ?? '',
    title: job?.title ?? '',
    officialId: job?.officialId ?? '',
    description: job?.description ?? '',
    location: job?.location ?? '',
    notes: job?.notes ?? '',
    status: job?.status ?? DEFAULT_JOB_STATUS,
    referralStatus: job?.referralStatus ?? DEFAULT_JOB_REFERRAL_STATUS,
    score: job?.score != null ? String(job.score) : '',
    analysis: job?.analysis ?? '',
  }
}

function toJobPayload(values: JobFormValues, isEdit: boolean): JobUpdateRequest {
  const payload: JobUpdateRequest = {
    url: cleanJobUrl(values.url),
    secondaryUrl: cleanJobUrl(values.secondaryUrl),
    companyName: values.companyName,
    title: values.title,
    officialId: values.officialId,
    description: values.description,
    location: values.location,
    notes: values.notes,
    status: values.status,
    referralStatus: values.referralStatus,
  }

  if (isEdit) {
    const trimmedScore = values.score.trim()
    payload.score = trimmedScore === '' ? null : Number(trimmedScore)
    payload.analysis = values.analysis
  }

  return payload
}

interface JobFormModalProps {
  job: Job | null
  onClose: () => void
  onSubmit: (payload: JobUpdateRequest) => void
  onDelete?: (job: Job) => void
  onGenerateResume?: (job: Job) => void
  isGeneratingResume?: boolean
}

export function JobFormModal({
  job,
  onClose,
  onSubmit,
  onDelete,
  onGenerateResume,
  isGeneratingResume,
}: JobFormModalProps) {
  const isEdit = job !== null

  const handleDelete = () => {
    if (!job) return
    onDelete?.(job)
  }

  const handleGenerateResume = () => {
    if (!job) return
    onGenerateResume?.(job)
  }

  return (
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className={styles.modal}>
        <div className={styles.headerRow}>
          <h2 className={styles.heading}>{isEdit ? 'Edit Job' : 'Add Job'}</h2>
          <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <Formik
          initialValues={jobToFormValues(job)}
          validationSchema={jobFormSchema}
          onSubmit={(values) => onSubmit(toJobPayload(values, isEdit))}
        >
          {({ errors, touched, values, setFieldValue, submitForm }) => (
            <Form
              className={styles.form}
              onKeyDown={(event: KeyboardEvent<HTMLFormElement>) => {
                if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                  event.preventDefault()
                  submitForm()
                }
              }}
            >
              {isEdit && (
                <>
                  <label className={styles.label}>
                    ID
                    <input className={styles.input} value={job.id} disabled />
                  </label>

                  <label className={styles.label}>
                    Created at
                    <input
                      className={styles.input}
                      value={dayjs(job.createdAt).format(CREATED_AT_FORMAT)}
                      disabled
                    />
                  </label>
                </>
              )}

              <label className={styles.label}>
                URL
                <Field name="url">
                  {({ field, form }: FieldProps<string>) => (
                    <input
                      {...field}
                      className={styles.input}
                      autoFocus
                      onBlur={(event: FocusEvent<HTMLInputElement>) => {
                        field.onBlur(event)
                        form.setFieldValue('url', cleanJobUrl(event.target.value))
                      }}
                    />
                  )}
                </Field>
                {touched.url && errors.url && <span className={styles.errorText}>{errors.url}</span>}
              </label>

              <label className={styles.label}>
                Company name
                <Field name="companyName" className={styles.input} />
              </label>

              <label className={styles.label}>
                Title
                <Field name="title" className={styles.input} />
              </label>

              <label className={styles.label}>
                Job ID
                <Field name="officialId" className={styles.input} />
              </label>

              <label className={styles.label}>
                Secondary URL
                <Field name="secondaryUrl">
                  {({ field, form }: FieldProps<string>) => (
                    <input
                      {...field}
                      className={styles.input}
                      onBlur={(event: FocusEvent<HTMLInputElement>) => {
                        field.onBlur(event)
                        form.setFieldValue('secondaryUrl', cleanJobUrl(event.target.value))
                      }}
                    />
                  )}
                </Field>
                {touched.secondaryUrl && errors.secondaryUrl && (
                  <span className={styles.errorText}>{errors.secondaryUrl}</span>
                )}
              </label>

              <label className={styles.label}>
                Job description
                <Field as="textarea" name="description" className={styles.input} rows={4} />
              </label>

              {isEdit && (
                <>
                  <label className={styles.label}>
                    Location
                    <Field name="location" className={styles.input} />
                  </label>

                  <label className={styles.label}>
                    Notes
                    <Field as="textarea" name="notes" className={styles.input} rows={3} />
                  </label>

                  <label className={styles.label}>
                    Score
                    <Field name="score" className={styles.input} />
                    {touched.score && errors.score && (
                      <span className={styles.errorText}>{errors.score}</span>
                    )}
                  </label>

                  <label className={styles.label}>
                    Analysis
                    <Field as="textarea" name="analysis" className={styles.input} rows={4} />
                  </label>
                </>
              )}

              <Dropdown
                label="Job status"
                value={values.status}
                onChange={(value) => setFieldValue('status', value)}
                options={STATUS_DROPDOWN_OPTIONS}
              />

              <Dropdown
                label="Referral status"
                value={values.referralStatus}
                onChange={(value) => setFieldValue('referralStatus', value)}
                options={REFERRAL_STATUS_DROPDOWN_OPTIONS}
              />

              {isEdit && (
                <label className={styles.label}>
                  Resume Generated
                  <input
                    className={styles.input}
                    value={job.isCustomResumeGenerated ? 'Yes' : 'No'}
                    disabled
                  />
                </label>
              )}

              <div className={styles.actions}>
                {isEdit && (
                  <button
                    type="button"
                    className={styles.deleteButton}
                    onClick={handleDelete}
                  >
                    Delete
                  </button>
                )}
                {isEdit && (
                  <button
                    type="button"
                    className={styles.generateResumeButton}
                    onClick={handleGenerateResume}
                    disabled={isGeneratingResume}
                  >
                    {isGeneratingResume ? 'Generating...' : 'Generate Resume'}
                  </button>
                )}
                <div className={styles.actionsSpacer} />
                <button type="button" className={styles.cancelButton} onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className={styles.submitButton}>
                  {isEdit ? 'Save' : 'Add'}
                </button>
              </div>
            </Form>
          )}
        </Formik>
      </div>
    </div>
  )
}
