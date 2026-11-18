import api from "./api";

export const slaService = {
  async listPolicies(params = {}) {
    const { data } = await api.get("/sla/policies/", { params });
    return data;
  },
  async createPolicy(payload) {
    const { data } = await api.post("/sla/policies/", payload);
    return data;
  },
  async updatePolicy(id, payload) {
    const { data } = await api.patch(`/sla/policies/${id}/`, payload);
    return data;
  },
  async getOverview() {
    const { data } = await api.get("/sla/overview/");
    return data;
  },
  async listEscalations(params = {}) {
    const { data } = await api.get("/sla/escalations/", { params });
    return data;
  },
  async acknowledgeEscalation(id) {
    const { data } = await api.post(`/sla/escalations/${id}/acknowledge/`);
    return data;
  },
};

export const knowledgeService = {
  async list(params = {}) {
    const { data } = await api.get("/knowledge/", { params });
    return data;
  },
  async get(id) {
    const { data } = await api.get(`/knowledge/${id}/`);
    return data;
  },
  async create(payload) {
    const { data } = await api.post("/knowledge/", payload);
    return data;
  },
  async update(id, payload) {
    const { data } = await api.patch(`/knowledge/${id}/`, payload);
    return data;
  },
  async publish(id) {
    const { data } = await api.post(`/knowledge/${id}/publish/`);
    return data;
  },
  async archive(id) {
    const { data } = await api.post(`/knowledge/${id}/archive/`);
    return data;
  },
  async recommend(ticketId) {
    const { data } = await api.get("/knowledge/recommend/", { params: { ticket_id: ticketId } });
    return data;
  },
};

export const analyticsService = {
  async getDashboard(params = {}) {
    const { data } = await api.get("/analytics/dashboard/", { params });
    return data;
  },
  async getPerformance(params = {}) {
    const { data } = await api.get("/analytics/performance/", { params });
    return data;
  },
  async downloadCSV(params = {}) {
    const response = await api.get("/analytics/export-csv/", { params, responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "helpdesk_tickets_report.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
  async listAuditLogs(params = {}) {
    const { data } = await api.get("/audit-logs/", { params });
    return data;
  },
};

export const aiService = {
  async classifyTicket(payload) {
    const { data } = await api.post("/ai/classify-ticket/", payload);
    return data;
  },
  async summarizeTicket(ticketId) {
    const { data } = await api.post("/ai/summarize-ticket/", { ticket_id: ticketId });
    return data;
  },
  async suggestSolutions(ticketId) {
    const { data } = await api.post("/ai/suggest-solutions/", { ticket_id: ticketId });
    return data;
  },
  async similarTickets(ticketId) {
    const { data } = await api.post("/ai/similar-tickets/", { ticket_id: ticketId });
    return data;
  },
};

export const notificationService = {
  async list(params = {}) {
    const { data } = await api.get("/notifications/", { params });
    return data;
  },
  async getUnreadCount() {
    const { data } = await api.get("/notifications/unread-count/");
    return data.unread_count;
  },
  async markRead(id) {
    const { data } = await api.post(`/notifications/${id}/read/`);
    return data;
  },
  async markAllRead() {
    const { data } = await api.post("/notifications/read-all/");
    return data;
  },
};
