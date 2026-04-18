import { didExpire, removeToken } from "../util/login";

export const BASE_URL = "http://localhost:5000";

export const maybeHandleExpire = (response: Response) => {
  if (didExpire(response)) {
    removeToken();
    window.location.href = "/";
  }
};
