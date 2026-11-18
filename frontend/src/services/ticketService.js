import api from "./api";

export const ticketService = {
  async list(params = {}) {
    const { data } = await api.get("/tickets/", { params });
    return data;
  },

  async get(id) {
    const { data } = await api.get(`/tickets/${id}/`);
    return data;
  },

  async create(payload) {
    const { data } = await api.post("/tickets/", payload);
    return data;
  },

  async update(id, payload) {
    const { data } = await api.patch(`/tickets/${id}/`, payload);
    return data;
  },

  async assign(id, payload) {
    const { data } = await api.post(`/tickets/${id}/assign/`, payload);
    return data;
  },

  async changeStatus(id, payload) {
    const { data } = await api.post(`/tickets/${id}/change-status/`, payload);
    return data;
  },

  async resolve(id, resolution_notes) {
    const { data } = await api.post(`/tickets/${id}/resolve/`, { resolution_notes });
    return data;
  },

  async reopen(id, reason) {
    const { data } = await api.post(`/tickets/${id}/reopen/`, { reason });
    return data;
  },

  async escalate(id, payload) {
    const { data } = await api.post(`/tickets/${id}/escalate/`, payload);
    return data;
  },

  async getHistory(id) {
    const { data } = await api.get(`/tickets/${id}/history/`);
    return data;
  },

  async getComments(id) {
    const { data } = await api.get(`/tickets/${id}/comments/`);
    return data;
  },

  async addComment(id, payload) {
    const { data } = await api.post(`/tickets/${id}/comments/`, payload);
    return data;
  },

  async getAttachments(id) {
    const { data } = await api.get(`/tickets/${id}/attachments/`);
    return data;
  },

  async uploadAttachment(id, file) {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post(`/tickets/${id}/attachments/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async downloadAttachment(attachmentId, filename) {
    const response = await api.get(`/attachments/${attachmentId}/download/`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
