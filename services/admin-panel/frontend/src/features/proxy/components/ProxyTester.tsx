import { useState, type JSX } from 'react';
import { sendProxyJsonRequest, type ProxyJsonRequest, type ProxyResponse } from '../api';

function isErrorResult(value: ProxyResponse | { error: string }): value is { error: string } {
  return typeof (value as { error?: unknown }).error === 'string';
}

const DEFAULT_JSON_REQUEST: ProxyJsonRequest = {
  service: 'contract-extractor',
  method: 'GET',
  endpoint: 'status',
};

type PayloadType = 'json' | 'plain-text' | '';
/**
 * Utility component that allows developers to send ad-hoc requests through the proxy service.
 */
export function ProxyTester() {
  const [request, setRequest] = useState<ProxyJsonRequest>(DEFAULT_JSON_REQUEST);
  const [result, setResult] = useState<ProxyResponse | { error: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [payload, setPayload] = useState('');
  const [payloadType, setPayloadType] = useState<PayloadType>('');

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
          try {
            body = JSON.parse(trimmedPayload) as unknown;
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

  const parseJsonValue = (value: unknown) => {
    if (typeof value === 'string') {
      try {
        return JSON.parse(value) as unknown;
      } catch {
        return value;
      }
    }

    return value;
  };

  const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value);

  const formatPrimitive = (value: unknown) => {
    if (value === null) {
      return 'null';
    }

    if (value === undefined) {
      return '—';
    }

    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }

    return formatJson(value);
  };

  function renderStructuredValue(value: unknown): JSX.Element {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="response-primitive">[]</span>;
      }

      return (
        <ul className="response-list nested">
          {value.map((item, index) => (
            <li key={index} className="response-item">
              <span className="response-key">#{index + 1}</span>
              <div className="response-value">{renderStructuredValue(item)}</div>
            </li>
          ))}
        </ul>
      );
    }

    if (isRecord(value)) {
      return renderEntries(Object.entries(value));
    }

    return <span className="response-primitive">{formatPrimitive(value)}</span>;
  }

  function renderEntries(entries: [string, unknown][]): JSX.Element {
    return (
      <ul className="response-list">
        {entries.map(([key, value]) => (
          <li key={key} className="response-item">
            <span className="response-key">{key}</span>
            <div className="response-value">{renderStructuredValue(value)}</div>
          </li>
        ))}
      </ul>
    );
  }

  function renderWarnings(value: unknown): JSX.Element {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="response-primitive">[]</span>;
      }

      return (
        <div className="warnings-collection">
          {value.map((item, index) => (
            <div key={index} className="warning-card">
              {isRecord(item) ? renderEntries(Object.entries(item)) : renderStructuredValue(item)}
            </div>
          ))}
        </div>
      );
    }

    return renderStructuredValue(value);
  }


  const renderDisabledFields = (value: unknown) => {
    const normalized: string[] = [];

    if (typeof value === 'string') {
      normalized.push(
        ...value
          .split(',')
          .map((item) => item.trim())
          .filter((item) => item.length > 0),
      );
    } else if (Array.isArray(value)) {
      normalized.push(
        ...value
          .map((item) => (typeof item === 'string' ? item.trim() : formatPrimitive(item)))
          .filter((item) => item.length > 0),
      );
    }

    if (normalized.length === 0) {
      return <span className="response-primitive">—</span>;
    }

    return (
      <ul className="response-simple-list">
        {normalized.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    );
  };

  const renderLlmRawOutputs = (value: unknown) => {
    if (!Array.isArray(value) || value.length === 0) {
      return <span className="response-primitive">—</span>;
    }

    return (
      <div className="llm-output-list">
        <pre className="json-block">{formatJson(value)}</pre>
      </div>
    );
  };

  const renderExtPrompt = (value: unknown) => {
    if (value === null || value === undefined) {
      return <span className="response-primitive">—</span>;
    }

    if (typeof value === 'string') {
      return <pre className="ext-prompt-block">{value}</pre>;
    }

    return <pre className="ext-prompt-block">{formatJson(value)}</pre>;
  };



  const renderDebugSection = (debugValue: unknown, extPromptValue?: unknown) => {
    // Объединяем debug + ext_prompt в единый объект для удобства
    const mergedDebug =
      isRecord(debugValue)
        ? { ...debugValue, ...(extPromptValue !== undefined ? { ext_prompt: extPromptValue } : {}) }
        : (extPromptValue !== undefined
          ? { ext_prompt: extPromptValue }
          : debugValue);

    if (!isRecord(mergedDebug)) {
      return renderStructuredValue(mergedDebug);
    }

    const debugRecord = mergedDebug as Record<string, unknown>;
    const debugPanels = [
      { key: 'disabled_fields', label: 'disabled_fields', render: renderDisabledFields },
      { key: 'llm_raw_outputs', label: 'llm_raw_outputs', render: renderLlmRawOutputs },
      { key: 'ext_prompt', label: 'ext_prompt', render: renderExtPrompt },
    ];

    const handledKeys = new Set(debugPanels.map(({ key }) => key));
    const otherEntries = Object.entries(debugRecord).filter(([key]) => !handledKeys.has(key));

    return (
      <div className="debug-section">
        {debugPanels.map(({ key, label, render }) =>
          key in debugRecord && debugRecord[key] !== undefined ? (
            <details key={key} className="debug-panel">
              <summary>{label}</summary>
              <div className="debug-panel-content">{render(debugRecord[key])}</div>
            </details>
          ) : null,
        )}
        {otherEntries.length > 0 && (
          <details className="debug-panel">
            <summary>Прочие данные</summary>
            <div className="debug-panel-content">{renderEntries(otherEntries)}</div>
          </details>
        )}
      </div>
    );
  };


  const parsedBody = result && !isErrorResult(result) ? parseJsonValue(result.body ?? result) : null;
  const structuredBody = isRecord(parsedBody) ? parsedBody : null;
  const dataSection = structuredBody?.['data'];
  const warningsSection = structuredBody?.['warnings'];
  const debugSection = structuredBody?.['debug'];
  const hasStructuredSections =
    structuredBody !== null &&
    ('data' in structuredBody || 'warnings' in structuredBody || 'debug' in structuredBody);

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
            <div className="payload-mode-item">
              <input
                type="radio"
                id="plain-text"
                name="payload-mode"
                value="plain-text"
                checked={payloadType === 'plain-text'}
                onChange={() => setPayloadType('plain-text')}
              />
              <label htmlFor="plain-text">text/plain</label>
            </div>
            <div className="payload-mode-item">
              <input
                type="radio"
                id="json"
                name="payload-mode"
                value="json"
                checked={payloadType === 'json'}
                onChange={() => setPayloadType('json')}
              />
              <label htmlFor="json">application/json</label>
            </div>
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
              {hasStructuredSections && structuredBody ? (
                <div className="response-sections">
                  {'data' in structuredBody && (
                    <div className="response-section">
                      <h4>data</h4>
                      {renderStructuredValue(dataSection)}
                    </div>
                  )}
                  {'warnings' in structuredBody && (
                    <div className="response-section">
                      <h4>warnings</h4>
                      {renderWarnings(warningsSection)}
                    </div>
                  )}
                  {('debug' in structuredBody || 'ext_prompt' in structuredBody) && (
                    <div className="response-section">
                      <h4>debug</h4>
                      {renderDebugSection(debugSection, structuredBody?.['ext_prompt'])}
                    </div>
                  )}
                </div>
              ) : (
                <pre className="json-block">{formatJson(result.body ?? result)}</pre>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}