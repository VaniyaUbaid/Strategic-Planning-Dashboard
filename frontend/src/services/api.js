const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function fetchJson(endpoint, options = {}) {
  const role = localStorage.getItem("platform_user_role") || "ADMINISTRATOR";
  const dept = localStorage.getItem("platform_user_department") || "";

  const headers = {
    "X-User-Role": role,
    ...(dept ? { "X-User-Department": dept } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `API Error: ${response.status} ${response.statusText}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function buildQueryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== null && val !== undefined && String(val).trim() !== "") {
      query.append(key, val);
    }
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export const api = {
  getHealth: () => fetchJson("/api/health"),
  getModulesStatus: () => fetchJson("/api/modules/status"),

  // Filter options APIs
  getStudentFilters: (params = {}) => fetchJson(`/api/students/filters${buildQueryString(params)}`),
  getAccessibleDepartments: () => fetchJson("/api/access/departments"),
  getAccessibleYears: (department) => fetchJson(`/api/access/years${buildQueryString({ department })}`),
  getAccessibleSemesters: (department, academicYear) =>
    fetchJson(`/api/access/semesters${buildQueryString({ department, academic_year: academicYear })}`),

  // Overview APIs
  getOverview: (params = {}) => fetchJson(`/api/overview${buildQueryString(params)}`),
  getAdminOverview: (params = {}) => fetchJson(`/api/admin/overview${buildQueryString(params)}`),
  getAdminAnalytics: (params = {}) => fetchJson(`/api/admin/analytics${buildQueryString(params)}`),
  getAdminStudents: (params = {}) => fetchJson(`/api/admin/students${buildQueryString(params)}`),

  // HOD APIs
  getHodOverview: (params = {}) => fetchJson(`/api/hod/overview${buildQueryString(params)}`),
  getHodStudents: (params = {}) => fetchJson(`/api/hod/students${buildQueryString(params)}`),

  // Teacher APIs
  getTeacherStudents: (params = {}) => fetchJson(`/api/teacher/students${buildQueryString(params)}`),

  // Student directory & detail APIs
  getStudents: (page = 1, pageSize = 20, filters = {}) =>
    fetchJson(`/api/students${buildQueryString({ page, page_size: pageSize, ...filters })}`),
  getStudentProfile: (studentId) => fetchJson(`/api/students/${studentId}`),
  getStudentRisk: (studentId) => fetchJson(`/api/students/${studentId}/risk`),
  getStudentHistory: (studentId) => fetchJson(`/api/students/${studentId}/history`),
  getStudentModelInsights: () => fetchJson("/api/students/analytics/model-insights"),

  // Finance Module APIs
  getFinanceStatus: () => fetchJson("/api/finance/status"),
  getFinanceFilters: () => fetchJson("/api/finance/filters"),
  getFinanceOverview: (params = {}) => fetchJson(`/api/finance/overview${buildQueryString(params)}`),
  getFinanceDepartments: (params = {}) => fetchJson(`/api/finance/departments${buildQueryString(params)}`),
  getFinanceTransactions: (params = {}) => fetchJson(`/api/finance/transactions${buildQueryString(params)}`),
  getFinanceBudget: (params = {}) => fetchJson(`/api/finance/budget${buildQueryString(params)}`),
  getFinanceFees: (params = {}) => fetchJson(`/api/finance/fees${buildQueryString(params)}`),
  getFinanceScholarships: (params = {}) => fetchJson(`/api/finance/scholarships${buildQueryString(params)}`),
  getFinanceRevenueExpense: (params = {}) => fetchJson(`/api/finance/revenue-expense${buildQueryString(params)}`),
  getFinanceRisk: (params = {}) => fetchJson(`/api/finance/risk${buildQueryString(params)}`),
  getResearchStatus: () => fetchJson("/api/research/status"),
  getResearchFilters: () => fetchJson("/api/research/filters"),
  getResearchOverview: (params = {}) => fetchJson(`/api/research/overview${buildQueryString(params)}`),
  getResearchDepartments: (params = {}) => fetchJson(`/api/research/departments${buildQueryString(params)}`),
  getResearchPrograms: (params = {}) => fetchJson(`/api/research/programs${buildQueryString(params)}`),
  getResearchPublications: (params = {}) => fetchJson(`/api/research/publications${buildQueryString(params)}`),
  getResearchParticipation: (params = {}) => fetchJson(`/api/research/participation${buildQueryString(params)}`),
  getDecisionStatus: () => fetchJson("/api/decision/status"),
  getDecisionOverview: (params = {}) => fetchJson(`/api/decision/overview${buildQueryString(params)}`),
  getDecisionInsights: (params = {}) => fetchJson(`/api/decision/insights${buildQueryString(params)}`),
  getDecisionRecommendations: (params = {}) => fetchJson(`/api/decision/recommendations${buildQueryString(params)}`),
  queryDecisionAssistant: (q, params = {}) => fetchJson(`/api/decision/query${buildQueryString({ q, ...params })}`),
};
