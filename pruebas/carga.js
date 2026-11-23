import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const hits = new Counter('backend_hits');
const valid = ['backend-1', 'backend-2', 'backend-3'];

export const options = {
  scenarios: {
    local: { executor: 'constant-arrival-rate', rate: 40, timeUnit: '1s',
      duration: '60s', preAllocatedVUs: 10, maxVUs: 40 },
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250'],
    checks: ['rate>0.99'],
    dropped_iterations: ['count==0'],
    'backend_hits{instancia:backend-1}': ['count>0'],
    'backend_hits{instancia:backend-2}': ['count>0'],
    'backend_hits{instancia:backend-3}': ['count>0'],
  },
};

export default function () {
  const response = http.get(__ENV.TEST_URL || 'http://127.0.0.1:8080/');
  let instance;
  if (response.status === 200) {
    try { instance = response.json('instancia'); } catch (_) { instance = undefined; }
  }
  if (valid.includes(instance)) hits.add(1, { instancia: instance });
  check(response, {
    'HTTP 200': (r) => r.status === 200,
    'réplica identificada': () => valid.includes(instance),
  });
}
