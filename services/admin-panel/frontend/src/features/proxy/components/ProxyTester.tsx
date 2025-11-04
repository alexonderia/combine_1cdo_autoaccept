import { useState } from 'react';
import { sendProxyFileRequest, sendProxyJsonRequest, type ProxyJsonRequest, type ProxyResponse } from '../api';

function isErrorResult(value: ProxyResponse | { error: string }): value is { error: string } {
  return typeof (value as { error?: unknown }).error === 'string';
}

const DEFAULT_JSON_REQUEST: ProxyJsonRequest = {
  service: 'contract-extractor',
  method: 'GET',
  endpoint: 'status',
};

/**
 * Utility component that allows developers to send ad-hoc requests through the proxy service.
 */
export function ProxyTester() {
  const [request, setRequest] = useState<ProxyJsonRequest>(DEFAULT_JSON_REQUEST);
  const [payload, setPayload] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ProxyResponse | { error: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (patch: Partial<ProxyJsonRequest>) => {
    setRequest((current) => ({ ...current, ...patch }));
  };

  const handleSend = async () => {
    setLoading(true);

    try {
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('service', request.service);
        formData.append('method', request.method);
        formData.append('endpoint', request.endpoint);
        const response = await sendProxyFileRequest(formData);
        setResult(response);
      } else {
        const body = payload.trim() ? JSON.parse(payload) : undefined;
        const response = await sendProxyJsonRequest({ ...request, body });
        setResult(response);
      }
    } catch (error) {
      setResult({ error: (error as Error).message });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (nextFile: File | null) => {
    setFile(nextFile);
    if (nextFile) {
      setPayload('');
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
        <select value={request.method} onChange={(event) => handleChange({ method: event.target.value })}>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
        </select>
      </div>

      <div className="form-group">
        <p>Endpoint:</p>
        <input value={request.endpoint} onChange={(event) => handleChange({ endpoint: event.target.value })} />
      </div>

      {request.method === 'POST' && (
        <div className="form-group">
          <p>Тело запроса (JSON):</p>
          <textarea rows={5} value={payload} onChange={(event) => setPayload(event.target.value)} />
          <p>ИЛИ выберите файл:</p>
          <input
            type="file"
            onChange={(event) => handleFileChange(event.target.files ? event.target.files[0] ?? null : null)}
          />
        </div>
      )}

      <button className="btn btn-primary form" onClick={handleSend} type="button" disabled={loading}>
        {loading ? 'Отправка...' : 'Отправить'}
      </button>

      {result && (
        <div className="result">
          <h3>Результат:</h3>

          {isErrorResult(result) ?(
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
