import api from "./api";

export const orgService = {
  // Users
  async listUsers(params = {}) {
    const { data } = await api.get("/users/", { params });
    return data;
  },
  async createUser(payload) {
    const { data } = await api.post("/users/", payload);
    return data;
  },
  async updateUser(id, payload) {
    const { data } = await api.patch(`/users/${id}/`, payload);
    return data;
  },
  async toggleUserActive(id) {
    const { data } = await api.post(`/users/${id}/toggle-active/`);
    return data;
  },

  // Departments
  async listDepartments(params = {}) {
    const { data } = await api.get("/departments/", { params });
    return data;
  },
  async createDepartment(payload) {
    const { data } = await api.post("/departments/", payload);
    return data;
  },
  async updateDepartment(id, payload) {
    const { data } = await api.patch(`/departments/${id}/`, payload);
    return data;
  },

  // Support Teams
  async listTeams(params = {}) {
    const { data } = await api.get("/teams/", { params });
    return data;
  },
  async createTeam(payload) {
    const { data } = await api.post("/teams/", payload);
    return data;
  },
  async addTeamMember(teamId, payload) {
    const { data } = await api.post(`/teams/${teamId}/members/`, payload);
    return data;
  },
  async removeTeamMember(teamId, userId) {
    await api.delete(`/teams/${teamId}/members/${userId}/`);
  },
};
