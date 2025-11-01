import { useState } from "react";
import { sendProxyRequest } from "../api";

export const ProxyTester = () => {
  const [service, setService] = useState("contract-extractor");
  const [method, setMethod] = useState("GET");
  const [endpoint, setEndpoint] = useState("status");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleSend = async () => {
    try {
      let data: any;

      if (file) {
        // Отправляем FormData с файлом
        const formData = new FormData();
        formData.append("file", file);
        formData.append("service", service);
        formData.append("method", method);
        formData.append("endpoint", endpoint);
        data = { body: formData };
        const res = await sendProxyRequest(data, true);
        setResult(res);
      } else {
        // Отправляем JSON из textarea
        let parsedBody = {};
        if (text.trim()) parsedBody = JSON.parse(text.trim());

        data = {
          service,
          method,
          endpoint,
          body: parsedBody,
        };
        const res = await sendProxyRequest(data);
        setResult(res);
      }

      setText("");
      setFile(null);
    } catch (err: any) {
      setResult({ error: err.message });
    }
  };

  const formatJson = (json: any) => {
    try {
      return JSON.stringify(JSON.parse(json), null, 2);
    } catch {
      return json;
    }
  };

  return (
    <div className="card">
      <h2>Тест запросов к сервисам</h2>

      <div className="form-group">
        <p>Сервис:</p>
        <select value={service} onChange={(e) => setService(e.target.value)}>
          <option value="contract-extractor">contract-extractor</option>
          <option value="legal-ai">legal-ai</option>
          <option value="globas-api">globas-api</option>
          <option value="m-base">m-base</option>
          <option value="base">base</option>
        </select>
      </div>

      <div className="form-group">
        <p>Метод:</p>
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="GET">GET</option>
          <option value="POST">POST</option>
        </select>
      </div>

      <div className="form-group">
        <p>Endpoint:</p>
        <input value={endpoint} onChange={(e) => setEndpoint(e.target.value)} />
      </div>

      {method === "POST" && (
        <div className="form-group">
          <p>Тело запроса (JSON):</p>
          <textarea
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <p>ИЛИ выберите файл:</p>
          <input
            type="file"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
            }}
          />
        </div>
      )}

      <button className="btn btn-primary form" onClick={handleSend}>Отправить</button>

      
      {result && (
        <div className="result">
          <h3>Результат:</h3>

          {result.error ? (
            <div className="error">❌ {result.error}</div>
          ) : (
            <>
              <div className="meta">
                <p>
                  <b>Статус:</b>{" "}
                  <span
                    className={
                      result.status_code >= 200 && result.status_code < 300
                        ? "status-ok"
                        : "status-bad"
                    }
                  >
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
                  <pre className="json-block">
                    {JSON.stringify(result.headers, null, 2)}
                  </pre>
                </div>
              )}
              <h4>Ответ:</h4>
              <pre className="json-block">
                {formatJson(result.body || JSON.stringify(result, null, 2))}
              </pre>
            </>
          )}
        </div>
      )}

      {result && (
        <div className="result">
          <h3>Результат в JSON:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
