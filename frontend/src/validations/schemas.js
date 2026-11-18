
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid corporate email address."),
  password: z.string().min(1, "Password is required."),
});

export const createTicketSchema = z.object({
  title: z.string().min(5, "Title must be at least 5 characters.").max(255),
  description: z.string().min(10, "Provide a clear description (at least 10 characters)."),
  category: z.enum(["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "EMAIL", "SECURITY", "OTHER"]),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  department: z.coerce.number().int().positive("Select a target department."),
  support_team: z.union([z.coerce.number().int().positive(), z.literal(""), z.null()]).optional(),
});

export const userCreateSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  first_name: z.string().min(1, "First name is required."),
  last_name: z.string().min(1, "Last name is required."),
  role: z.enum(["ADMIN", "MANAGER", "ENGINEER", "EMPLOYEE"]),
  job_title: z.string().optional(),
  phone: z.string().optional(),
  department: z.union([z.coerce.number().int().positive(), z.literal(""), z.null()]).optional(),
  password: z.string().min(10, "Password must be at least 10 characters."),
});

export const departmentSchema = z.object({
  name: z.string().min(2, "Department name is required."),
  code: z.string().min(2, "Code is required.").max(20),
  description: z.string().optional(),
  manager: z.union([z.coerce.number().int().positive(), z.literal(""), z.null()]).optional(),
});

export const teamSchema = z.object({
  name: z.string().min(2, "Team name is required."),
  department: z.coerce.number().int().positive("Department is required."),
  lead: z.union([z.coerce.number().int().positive(), z.literal(""), z.null()]).optional(),
  description: z.string().optional(),
});

export const slaPolicySchema = z.object({
  name: z.string().min(3, "Policy name is required."),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  department: z.coerce.number().int().positive("Select a department."),
  first_response_minutes: z.coerce.number().int().min(1),
  resolution_minutes: z.coerce.number().int().min(5),
  escalation_threshold_pct: z.coerce.number().int().min(10).max(99),
  business_hours_only: z.boolean().default(false),
});

export const knowledgeArticleSchema = z.object({
  title: z.string().min(5, "Article title is required."),
  category: z.enum(["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "EMAIL", "SECURITY", "OTHER"]),
  summary: z.string().min(10, "Summary is required."),
  content: z.string().min(20, "Article content is required."),
  troubleshooting_steps: z.string().optional(),
});
