import type { FocusEvent } from 'react'

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
import type { JobCreateRequest, JobFormValues } from '../interfaces/job.interfaces'
import type { Job } from '../types/job.types'
import { cleanJobUrl } from '../utils/urlCleaner'
import styles from './JobFormModal.module.css'

const CREATED_AT_FORMAT = 'DD MMM YYYY'

const jobFormSchema = Yup.object({
  url: Yup.string().trim(),
  companyName: Yup.string(),
  title: Yup.string(),
  officialId: Yup.string(),
  description: Yup.string(),
  location: Yup.string(),
  minYears: Yup.number().optional(),
  maxYears: Yup.number().optional(),
  notes: Yup.string(),
  status: Yup.string().oneOf(JOB_STATUS_OPTIONS).required(),
  referralStatus: Yup.string().oneOf(JOB_REFERRAL_STATUS_OPTIONS).required(),
})

function jobToFormValues(job: Job | null): JobFormValues {
  return {
    url: job?.url ?? '',
    companyName: job?.companyName ?? '',
    title: job?.title ?? '',
    officialId: job?.officialId ?? '',
    description: job?.description ?? '',
    location: job?.location ?? '',
    minYears: job?.minYears?.toString() ?? '',
    maxYears: job?.maxYears?.toString() ?? '',
    notes: job?.notes ?? '',
    status: job?.status ?? DEFAULT_JOB_STATUS,
    referralStatus: job?.referralStatus ?? DEFAULT_JOB_REFERRAL_STATUS,
  }
}

function toJobPayload(values: JobFormValues): JobCreateRequest {
  return {
    url: cleanJobUrl(values.url),
    companyName: values.companyName,
    title: values.title,
    officialId: values.officialId,
    description: values.description,
    location: values.location,
    minYears: values.minYears === '' ? undefined : Number(values.minYears),
    maxYears: values.maxYears === '' ? undefined : Number(values.maxYears),
    notes: values.notes,
    status: values.status,
    referralStatus: values.referralStatus,
  }
}

interface JobFormModalProps {
  job: Job | null
  onClose: () => void
  onSubmit: (payload: JobCreateRequest) => void
}

export function JobFormModal({ job, onClose, onSubmit }: JobFormModalProps) {
  const isEdit = job !== null

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
          onSubmit={(values) => onSubmit(toJobPayload(values))}
        >
          {({ errors, touched, values, setFieldValue }) => (
            <Form className={styles.form}>
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
                URL *
                <Field name="url">
                  {({ field, form }: FieldProps<string>) => (
                    <input
                      {...field}
                      className={styles.input}
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
                    Min years
                    <Field name="minYears" type="number" className={styles.input} />
                  </label>

                  <label className={styles.label}>
                    Max years
                    <Field name="maxYears" type="number" className={styles.input} />
                  </label>

                  <label className={styles.label}>
                    Notes
                    <Field as="textarea" name="notes" className={styles.input} rows={3} />
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

              <div className={styles.actions}>
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
