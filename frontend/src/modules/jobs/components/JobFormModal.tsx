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

const jobFormSchema = Yup.object({
  url: Yup.string().trim().required('URL is required'),
  company_name: Yup.string(),
  title: Yup.string(),
  official_id: Yup.string(),
  description: Yup.string(),
  status: Yup.string().oneOf(JOB_STATUS_OPTIONS).required(),
  referral_status: Yup.string().oneOf(JOB_REFERRAL_STATUS_OPTIONS).required(),
})

function jobToFormValues(job: Job | null): JobFormValues {
  return {
    url: job?.url ?? '',
    company_name: job?.company_name ?? '',
    title: job?.title ?? '',
    official_id: job?.official_id ?? '',
    description: job?.description ?? '',
    status: job?.status ?? DEFAULT_JOB_STATUS,
    referral_status: job?.referral_status ?? DEFAULT_JOB_REFERRAL_STATUS,
  }
}

interface JobFormModalProps {
  job: Job | null
  onClose: () => void
  onSubmit: (values: JobFormValues) => void
}

const INPUT_CLASS = 'mt-1 w-full rounded border border-gray-300 px-2 py-1'
const LABEL_CLASS = 'flex flex-col text-sm'

export function JobFormModal({ job, onClose, onSubmit }: JobFormModalProps) {
  const isEdit = job !== null

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-semibold">{isEdit ? 'Edit Job' : 'Add Job'}</h2>

        <Formik
          initialValues={jobToFormValues(job)}
          validationSchema={jobFormSchema}
          onSubmit={(values) => onSubmit({ ...values, url: cleanJobUrl(values.url) })}
        >
          {({ errors, touched }) => (
            <Form className="flex flex-col gap-3">
              <label className={LABEL_CLASS}>
                URL *
                <Field name="url">
                  {({ field, form }: FieldProps<string>) => (
                    <input
                      {...field}
                      className={INPUT_CLASS}
                      onBlur={(event: FocusEvent<HTMLInputElement>) => {
                        field.onBlur(event)
                        form.setFieldValue('url', cleanJobUrl(event.target.value))
                      }}
                    />
                  )}
                </Field>
                {touched.url && errors.url && (
                  <span className="text-xs text-red-600">{errors.url}</span>
                )}
              </label>

              <label className={LABEL_CLASS}>
                Company name
                <Field name="company_name" className={INPUT_CLASS} />
              </label>

              <label className={LABEL_CLASS}>
                Title
                <Field name="title" className={INPUT_CLASS} />
              </label>

              <label className={LABEL_CLASS}>
                Job ID
                <Field name="official_id" className={INPUT_CLASS} />
              </label>

              <label className={LABEL_CLASS}>
                Job description
                <Field as="textarea" name="description" className={INPUT_CLASS} rows={4} />
              </label>

              <label className={LABEL_CLASS}>
                Job status
                <Field as="select" name="status" className={INPUT_CLASS}>
                  {JOB_STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Field>
              </label>

              <label className={LABEL_CLASS}>
                Referral status
                <Field as="select" name="referral_status" className={INPUT_CLASS}>
                  {JOB_REFERRAL_STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Field>
              </label>

              <div className="mt-2 flex justify-end gap-2">
                <button
                  type="button"
                  className="rounded border border-gray-300 px-3 py-1 text-sm"
                  onClick={onClose}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                >
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
