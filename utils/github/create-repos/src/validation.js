import zod from 'zod';  

const VALID_PERMISSIONS = ['pull', 'triage', 'push', 'maintain', 'admin'];

const ERROR_USERS = "name is required - it is the GitHub username";
const ERROR_TEAMS = "slug is required - it is the GitHub team slug";

const repoSchema = zod.array(zod.object({
  name: zod.string().min(1),
  users: zod.array(zod.object({
    name: zod.string(ERROR_USERS).min(1, ERROR_USERS),
    permission: zod.enum(VALID_PERMISSIONS, "Permission is required"),
  })).optional(),
  teams: zod.array(zod.object({
    slug: zod.string(ERROR_TEAMS).min(1, ERROR_TEAMS),
    permission: zod.enum(VALID_PERMISSIONS, "Permission is required"),
  })).optional()
}).refine((data) => data.users !== undefined || data.teams !== undefined, {
    message: "You must specify at least one user or team."
}));
    
export function validateJSONFile(json) {
  const result = repoSchema.safeParse(json);
  if (!result.success) {
    throw result.error;   
  }
  return result.data;    
}
