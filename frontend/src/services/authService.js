import api, { TOKEN_STORAGE } from "./api";

export const authService = {
  async login(email, password) {
    const { data } = await api.post("/auth/login/", { email, password });
    localStorage.setItem(TOKEN_STORAGE.ACCESS, data.access);
    localStorage.setItem(TOKEN_STORAGE.REFRESH, data.refresh);
    return data.user;
  },

  async logout() {
    const refresh = localStorage.getItem(TOKEN_STORAGE.REFRESH);
    try {
      if (refresh) {
        await api.post("/auth/logout/", { refresh });
      }
    } finally {
      localStorage.removeItem(TOKEN_STORAGE.ACCESS);
      localStorage.removeItem(TOKEN_STORAGE.REFRESH);
    }
  },

  async getMe() {
    const { data } = await api.get("/auth/me/");
    return data;
  },

  async updateProfile(payload) {
    const { data } = await api.patch("/auth/me/", payload);
    return data;
  },

  async changePassword(payload) {
    const { data } = await api.post("/auth/change-password/", payload);
    return data;
  },
};
