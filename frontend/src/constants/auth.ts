export const officialAPIEndpoint = 'https://api.openai.com/v1/chat/completions';
const customAPIEndpoint =
  import.meta.env.VITE_CUSTOM_API_ENDPOINT || 'https://chatgpt-api.shn.hk/v1/';
export const defaultAPIEndpoint =
  import.meta.env.VITE_DEFAULT_API_ENDPOINT || 'https://prj-tourism-route-planner-1.onrender.com/v1/chat/completions';

export const availableEndpoints = [officialAPIEndpoint, customAPIEndpoint];
