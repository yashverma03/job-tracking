import type { FocusEvent } from 'react'

import { Formik, Form, Field, type FieldProps } from 'formik'
import * as Yup from 'yup'

import {
  DEFAULT_JOB_REFERRAL_STATUS,
  DEFAULT_JOB_STATUS,
  JOB_REFERRAL_STATUS_OPTIONS,
  JOB_STATUS_OPTIONS,
} from '../constants/job.constants'
import type { JobFormValues } from '../interfaces/job.interfaces'
import type { Job } from '../types/job.types'
import { cleanJobUrl } from '../utils/urlCleaner'
import styles from './JobFormModal.module.css'

const jobFormSchema = Yup.object({
  url: Yup.string().trim().required('URL is required'),
  companyName: Yup.string(),
  title: Yup.string(),
  officialId: Yup.string(),
  description: Yup.string(),
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
    status: job?.status ?? DEFAULT_JOB_STATUS,
    referralStatus: job?.referralStatus ?? DEFAULT_JOB_REFERRAL_STATUS,
  }
}

interface JobFormModalProps {
  job: Job | null
  onClose: () => void
  onSubmit: (values: JobFormValues) => void
}

export function JobFormModal({ job, onClose, onSubmit }: JobFormModalProps) {
  const isEdit = job !== null

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h2 className={styles.heading}>{isEdit ? 'Edit Job' : 'Add Job'}</h2>

        <Formik
          initialValues={jobToFormValues(job)}
          validationSchema={jobFormSchema}
          onSubmit={(values) => onSubmit({ ...values, url: cleanJobUrl(values.url) })}
        >
          {({ errors, touched }) => (
            <Form className={styles.form}>
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

              <label className={styles.label}>
                Job status
                <Field as="select" name="status" className={styles.input}>
                  {JOB_STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Field>
              </label>

              <label className={styles.label}>
                Referral status
                <Field as="select" name="referralStatus" className={styles.input}>
                  {JOB_REFERRAL_STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Field>
              </label>

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
