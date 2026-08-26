import { DEFAULT_PAGE_SIZE } from '../../../common/constants/pagination.constants';
import type { JobListQueryParams } from '../interfaces/job.interfaces';
import type { JobReferralStatus, JobStatus, JobsViewMode } from '../types/job.types';

const DEFAULT_MODE: JobsViewMode = 'all';

export function parseFiltersFromSearchParams(
  searchParams: URLSearchParams,
): JobListQueryParams {
  const status = searchParams.getAll('status');
  const referralStatus = searchParams.getAll('referralStatus');
  const search = searchParams.get('search');
  const dateFrom = searchParams.get('dateFrom');
  const dateTo = searchParams.get('dateTo');
  const page = Number(searchParams.get('page'));
  const limit = Number(searchParams.get('limit'));

  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    limit: Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_PAGE_SIZE,
    status: status.length ? (status as JobStatus[]) : undefined,
    referralStatus: referralStatus.length
      ? (referralStatus as JobReferralStatus[])
      : undefined,
    search: search ?? undefined,
    dateFrom: dateFrom ?? undefined,
    dateTo: dateTo ?? undefined,
  };
}

export function parseModeFromSearchParams(
  searchParams: URLSearchParams,
): JobsViewMode {
  const mode = searchParams.get('mode');
  if (mode === 'apply' || mode === 'referral' || mode === 'all') return mode;
  return DEFAULT_MODE;
}

export function buildSearchParams(
  filters: JobListQueryParams,
  mode: JobsViewMode,
): URLSearchParams {
  const params = new URLSearchParams();

  if (mode !== DEFAULT_MODE) params.set('mode', mode);
  if (filters.page && filters.page !== 1) params.set('page', String(filters.page));
  if (filters.limit && filters.limit !== DEFAULT_PAGE_SIZE) {
    params.set('limit', String(filters.limit));
  }
  filters.status?.forEach((value) => params.append('status', value));
  filters.referralStatus?.forEach((value) =>
    params.append('referralStatus', value),
  );
  if (filters.search) params.set('search', filters.search);
  if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
  if (filters.dateTo) params.set('dateTo', filters.dateTo);

  return params;
}
