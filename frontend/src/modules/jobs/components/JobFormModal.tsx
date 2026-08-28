import { useEffect, type FocusEvent } from 'react';

import dayjs from 'dayjs';
import { Formik, Form, Field, type FieldProps } from 'formik';
import { X } from 'lucide-react';
import * as Yup from 'yup';

import { fetchCompanyNameByUrl } from '../../../common/api/jobs/jobs.service';
import { ComboBox } from '../../../common/components/ComboBox';
import { Dropdown } from '../../../common/components/Dropdown';
import { useDebouncedValue } from '../../../common/hooks/useDebouncedValue';
import {
  DEFAULT_JOB_REFERRAL_STATUS,
  DEFAULT_JOB_STATUS,
  JOB_REFERRAL_STATUS_OPTIONS,
  JOB_STATUS_OPTIONS,
  REFERRAL_STATUS_DROPDOWN_OPTIONS,
  STATUS_DROPDOWN_OPTIONS,
} from '../constants/job.constants';
import {
  useCompanyNamesQuery,
  useJobTitlesQuery,
} from '../hooks/useJobSuggestionsQuery';
import type {
  JobFormValues,
  JobUpdateRequest,
} from '../interfaces/job.interfaces';
import type { Job, JobStatus } from '../types/job.types';
import { cleanJobUrl } from '../utils/urlCleaner';
import styles from './JobFormModal.module.css';

const CREATED_AT_FORMAT = 'DD MMM YYYY';
const DEFAULT_JOB_TITLE = 'Software Engineer';

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
  score: Yup.string()
    .trim()
    .matches(/^-?\d*$/, 'Score must be a whole number'),
  analysis: Yup.string(),
});

export interface JobCloneSource {
  companyName: string | null;
  title: string | null;
  status: JobStatus;
  referralStatus: Job['referralStatus'];
}

function jobToFormValues(
  job: Job | null,
  cloneFrom?: JobCloneSource | null,
): JobFormValues {
  if (job) {
    return {
      url: job.url ?? '',
      secondaryUrl: job.secondaryUrl ?? '',
      companyName: job.companyName ?? '',
      title: job.title ?? '',
      officialId: job.officialId ?? '',
      description: job.description ?? '',
      location: job.location ?? '',
      notes: job.notes ?? '',
      status: job.status,
      referralStatus: job.referralStatus,
      score: job.score != null ? String(job.score) : '',
      analysis: job.analysis ?? '',
    };
  }

  return {
    url: '',
    secondaryUrl: '',
    companyName: cloneFrom?.companyName ?? '',
    title: cloneFrom?.title ?? '',
    officialId: '',
    description: '',
    location: '',
    notes: '',
    status: cloneFrom?.status ?? DEFAULT_JOB_STATUS,
    referralStatus: cloneFrom?.referralStatus ?? DEFAULT_JOB_REFERRAL_STATUS,
    score: '',
    analysis: '',
  };
}

function toJobPayload(
  values: JobFormValues,
  isEdit: boolean,
): JobUpdateRequest {
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
  };

  if (isEdit) {
    const trimmedScore = values.score.trim();
    payload.score = trimmedScore === '' ? null : Number(trimmedScore);
    payload.analysis = values.analysis;
  }

  return payload;
}

// interface AutoReferralDefaultProps {
//   companyName: string;
//   title: string;
//   officialId: string;
//   referralStatus: JobFormValues['referralStatus'];
//   setFieldValue: (field: string, value: string) => void;
// }

// const REFERRAL_REQUIRED_STATUS = 'Referral required' as const;

// function AutoReferralDefault({
//   companyName,
//   title,
//   officialId,
//   referralStatus,
//   setFieldValue,
// }: AutoReferralDefaultProps) {
//   const hasAutoApplied = useRef(false);
//
//   useEffect(() => {
//     if (hasAutoApplied.current) return;
//     const hasIdentifyingInfo = Boolean(
//       companyName.trim() || title.trim() || officialId.trim(),
//     );
//     if (!hasIdentifyingInfo) return;
//
//     hasAutoApplied.current = true;
//     if (referralStatus === DEFAULT_JOB_REFERRAL_STATUS) {
//       setFieldValue('referralStatus', REFERRAL_REQUIRED_STATUS);
//     }
//   }, [companyName, title, officialId, referralStatus, setFieldValue]);
//
//   return null;
// }

interface CompanyNameFieldProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (value: string) => void;
}

function CompanyNameField({ value, onChange, onSelect }: CompanyNameFieldProps) {
  const debouncedValue = useDebouncedValue(value, 300);
  const { data: companyNames = [] } = useCompanyNamesQuery(debouncedValue);

  return (
    <ComboBox
      label="Company name"
      value={value}
      onChange={onChange}
      onSelect={onSelect}
      options={companyNames}
    />
  );
}

interface JobTitleFieldProps {
  value: string;
  onChange: (value: string) => void;
}

function JobTitleField({ value, onChange }: JobTitleFieldProps) {
  const debouncedValue = useDebouncedValue(value, 300);
  const { data: jobTitles = [] } = useJobTitlesQuery(debouncedValue);

  return (
    <ComboBox
      label="Title"
      value={value}
      onChange={onChange}
      options={jobTitles}
    />
  );
}

function SubmitOnCtrlEnter({ submitForm }: { submitForm: () => void }) {
  useEffect(() => {
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        submitForm();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [submitForm]);

  return null;
}

interface JobFormModalProps {
  job: Job | null;
  cloneFrom?: JobCloneSource | null;
  onClose: () => void;
  onSubmit: (payload: JobUpdateRequest) => void;
  onDelete?: (job: Job) => void;
  onGenerateResume?: (job: Job) => void;
  isGeneratingResume?: boolean;
}

export function JobFormModal({
  job,
  cloneFrom,
  onClose,
  onSubmit,
  onDelete,
  onGenerateResume,
  isGeneratingResume,
}: JobFormModalProps) {
  const isEdit = job !== null;

  const handleDelete = () => {
    if (!job) return;
    onDelete?.(job);
  };

  const handleGenerateResume = () => {
    if (!job) return;
    onGenerateResume?.(job);
  };

  return (
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className={styles.modal}>
        <div className={styles.headerRow}>
          <h2 className={styles.heading}>{isEdit ? 'Edit Job' : 'Add Job'}</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <Formik
          initialValues={jobToFormValues(job, cloneFrom)}
          validationSchema={jobFormSchema}
          onSubmit={(values) => onSubmit(toJobPayload(values, isEdit))}
        >
          {({ errors, touched, values, setFieldValue, submitForm }) => (
            <Form className={styles.form}>
              <SubmitOnCtrlEnter submitForm={submitForm} />

              {/* {!isEdit && !cloneFrom && (
                <AutoReferralDefault
                  companyName={values.companyName}
                  title={values.title}
                  officialId={values.officialId}
                  referralStatus={values.referralStatus}
                  setFieldValue={setFieldValue}
                />
              )} */}

              {isEdit && (
                <div className={styles.row}>
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
                </div>
              )}

              <label className={styles.label}>
                URL
                <Field name="url">
                  {({ field, form }: FieldProps<string>) => (
                    <input
                      {...field}
                      className={styles.input}
                      autoFocus
                      onBlur={async (event: FocusEvent<HTMLInputElement>) => {
                        field.onBlur(event);
                        const cleanedUrl = cleanJobUrl(event.target.value);
                        form.setFieldValue('url', cleanedUrl);

                        if (!cleanedUrl || form.values.companyName.trim())
                          return;
                        const companyName =
                          await fetchCompanyNameByUrl(cleanedUrl);
                        if (companyName && !form.values.companyName.trim()) {
                          form.setFieldValue('companyName', companyName);
                          if (!form.values.title.trim()) {
                            form.setFieldValue('title', DEFAULT_JOB_TITLE);
                          }
                        }
                      }}
                    />
                  )}
                </Field>
                {touched.url && errors.url && (
                  <span className={styles.errorText}>{errors.url}</span>
                )}
              </label>

              <div className={styles.row}>
                <CompanyNameField
                  value={values.companyName}
                  onChange={(value) => setFieldValue('companyName', value)}
                  onSelect={() => {
                    if (!values.title.trim()) {
                      setFieldValue('title', DEFAULT_JOB_TITLE);
                    }
                  }}
                />

                <JobTitleField
                  value={values.title}
                  onChange={(value) => setFieldValue('title', value)}
                />
              </div>

              <div className={styles.row}>
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
                          field.onBlur(event);
                          form.setFieldValue(
                            'secondaryUrl',
                            cleanJobUrl(event.target.value),
                          );
                        }}
                      />
                    )}
                  </Field>
                  {touched.secondaryUrl && errors.secondaryUrl && (
                    <span className={styles.errorText}>
                      {errors.secondaryUrl}
                    </span>
                  )}
                </label>
              </div>

              <label className={styles.label}>
                Job description
                <Field
                  as="textarea"
                  name="description"
                  className={styles.input}
                  rows={2}
                />
              </label>

              {isEdit && (
                <>
                  <div className={styles.row}>
                    <label className={styles.label}>
                      Location
                      <Field name="location" className={styles.input} />
                    </label>

                    <label className={styles.label}>
                      Score
                      <Field name="score" className={styles.input} />
                      {touched.score && errors.score && (
                        <span className={styles.errorText}>
                          {errors.score}
                        </span>
                      )}
                    </label>
                  </div>

                  <label className={styles.label}>
                    Notes
                    <Field
                      as="textarea"
                      name="notes"
                      className={styles.input}
                      rows={1}
                    />
                  </label>

                  <div className={styles.row}>
                    <label className={styles.label}>
                      Analysis
                      <Field
                        as="textarea"
                        name="analysis"
                        className={styles.input}
                        rows={1}
                      />
                    </label>

                    <label className={styles.label}>
                      Resume Generated
                      <input
                        className={styles.input}
                        value={job.isCustomResumeGenerated ? 'Yes' : 'No'}
                        disabled
                      />
                    </label>
                  </div>
                </>
              )}

              <div className={styles.row}>
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
              </div>

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
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={onClose}
                >
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
  );
}
