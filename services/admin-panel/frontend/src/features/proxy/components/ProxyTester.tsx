import { useState } from 'react';
import { sendProxyJsonRequest, type ProxyJsonRequest, type ProxyResponse } from '../api';

function isErrorResult(value: ProxyResponse | { error: string }): value is { error: string } {
  return typeof (value as { error?: unknown }).error === 'string';
}

const DEFAULT_JSON_REQUEST: ProxyJsonRequest = {
  service: 'contract-extractor',
  method: 'GET',
  endpoint: 'status',
};

type PayloadType = 'json' | 'plain-text';
/**
 * Utility component that allows developers to send ad-hoc requests through the proxy service.
 */
export function ProxyTester() {
  const [request, setRequest] = useState<ProxyJsonRequest>(DEFAULT_JSON_REQUEST);
  const [result, setResult] = useState<ProxyResponse | { error: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [payload, setPayload] = useState('');
  const [payloadType, setPayloadType] = useState<PayloadType>('plain-text');

  const handleChange = (patch: Partial<ProxyJsonRequest>) => {
    setRequest((current) => ({ ...current, ...patch }));
    if (patch.method && patch.method === 'GET') {
      setPayload('');
      setPayloadType('plain-text');
    }
  };

  const handleSend = async () => {
    setResult(null);
    setLoading(true);

    try {
      let params: Record<string, unknown> | undefined;
      const trimmedQuery = query.trim();

      if (trimmedQuery) {
        try {
          const parsed = JSON.parse(trimmedQuery) as unknown;
          if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
            params = parsed as Record<string, unknown>;
          } else {
            setResult({ error: 'Query-параметры должны быть JSON-объектом.' });
            return;
          }
        } catch (error) {
          setResult({ error: `Ошибка парсинга JSON: ${(error as Error).message}` });
          return;
        }
      }
    
      let body: unknown;
      let contentType: string | undefined;

      if (request.method === 'POST') {
        const trimmedPayload = payload.trim();
        if (!trimmedPayload) {
          setResult({ error: 'Добавьте тело POST-запроса.' });
          return;
        }
        if (payloadType === 'plain-text') {
          body = trimmedPayload;
          contentType = 'text/plain';
        } else {
          try {body = JSON.parse(trimmedPayload) as unknown;
            contentType = 'application/json';
          } catch (error) {
            setResult({ error: `Ошибка парсинга JSON: ${(error as Error).message}` });
            return;
          }
        }
      }
      const response = await sendProxyJsonRequest({ ...request, params, body, contentType });
      setResult(response);
    } catch (error) {
      setResult({ error: (error as Error).message });
    } finally {
      setLoading(false);
    }
  };

  const formatJson = (value: unknown) => {
    if (typeof value === 'string') {
      try {
        return JSON.stringify(JSON.parse(value), null, 2);
      } catch {
        return value;
      }
    }

    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  };

  return (
    <div className="card">
      <h2>Тест запросов к сервисам</h2>

      <div className="form-group">
        <p>Сервис:</p>
        <select value={request.service} onChange={(event) => handleChange({ service: event.target.value })}>
          <option value="contract-extractor">contract-extractor</option>
          <option value="legal-ai">legal-ai</option>
          <option value="globas-api">globas-api</option>
          <option value="m-base">m-base</option>
          <option value="base">base</option>
        </select>
      </div>

      <div className="form-group">
        <p>Метод:</p>
        <select value={request.method} onChange={(event) => handleChange({ method: event.target.value as 'GET' | 'POST' })}>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
        </select>
      </div>

      <div className="form-group">
        <p>Endpoint:</p>
        <input value={request.endpoint} onChange={(event) => handleChange({ endpoint: event.target.value })} />
      </div>

      <div className="form-group">
        <p>Query-параметры (JSON):</p>
        <textarea
          rows={5}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Введите JSON-объект с query-параметрами (опционально)."
        />
      </div>

      {request.method === 'POST' && (
        <div className="form-group">
          <p>Тело запроса:</p>
          <div className="payload-mode">
            <label>
              <input
                type="radio"
                name="payload-mode"
                value="plain-text"
                checked={payloadType === 'plain-text'}
                onChange={() => setPayloadType('plain-text')}
              />
              text/plain
            </label>
            <label>
              <input
                type="radio"
                name="payload-mode"
                value="json"
                checked={payloadType === 'json'}
                onChange={() => setPayloadType('json')}
              />
              application/json
            </label>
          </div>
          <textarea
            rows={5}
            value={payload}
            onChange={(event) => setPayload(event.target.value)}
            placeholder={
              payloadType === 'plain-text'
              ? 'Введите текст, который будет отправлен как text/plain.'
                : 'Введите JSON-тело POST-запроса.'
            }
          />
           </div>
      )}

      <button className="btn btn-primary form" onClick={handleSend} type="button" disabled={loading}>
        {loading ? 'Отправка...' : 'Отправить'}
      </button>

      {result && (
        <div className="result">
          <h3>Результат:</h3>

          {isErrorResult(result) ? (
            <div className="error">❌ {result.error}</div>
          ) : (
            <>
              <div className="meta">
                <p>
                  <b>Статус:</b>{' '}
                  <span className={result.status_code >= 200 && result.status_code < 300 ? 'status-ok' : 'status-bad'}>
                    {result.status_code}
                  </span>
                </p>
                <p>
                  <b>URL:</b> {result.url}
                </p>
              </div>

              {result.headers && (
                <div className="headers-block">
                  <h4>Заголовки:</h4>
                  <pre className="json-block">{formatJson(result.headers)}</pre>
                </div>
              )}

              <h4>Ответ:</h4>
              <pre className="json-block">{formatJson(result.body ?? result)}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
