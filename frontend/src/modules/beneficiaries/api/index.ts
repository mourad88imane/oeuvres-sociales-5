import apiClient from "@shared/api/apiClient";
import { useQuery } from "@tanstack/react-query";
import type { GlobalBeneficiaryResponse } from "../types";

interface BeneficiaryFilters {
  page?: number;
  page_size?: number;
  search?: string;
  relationship?: string;
  eligible?: string;
}

export const beneficiaryGlobalApi = {
  list: (params: BeneficiaryFilters = {}) =>
    apiClient.get<GlobalBeneficiaryResponse>("/beneficiaries/", { params }),
};

export const BENEFICIARY_KEYS = {
  list: (f: BeneficiaryFilters = {}) => ["beneficiaries", "list", f] as const,
};

export function useBeneficiaries(filters: BeneficiaryFilters = {}) {
  return useQuery({
    queryKey: BENEFICIARY_KEYS.list(filters),
    queryFn: () => beneficiaryGlobalApi.list(filters).then(r => r.data),
    placeholderData: (prev) => prev,
  });
}
