#!/usr/bin/env python3
"""
Enhanced Templates for Multi-Language SDK Generation
Complete templates for TypeScript, Java, Go, Rust, Swift, and additional modern languages
"""

class EnhancedTemplateEngine:
    """Enhanced template engine with complete implementations for all supported languages"""

    def get_typescript_client_template(self) -> str:
        """Complete TypeScript client template"""
        return '''/**
 * {{ package_name }} - {{ description }}
 * Generated TypeScript API client for {{ base_url }}
 */

{% if include_type_hints %}
export interface APIResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export interface RequestConfig {
  timeout?: number;
  retries?: number;
  headers?: Record<string, string>;
}

{% for endpoint in endpoints %}
export interface {{ endpoint.operation_id|title }}Request {
  {% for param in endpoint.parameters %}
  {{ param.name }}{% if not param.required %}?{% endif %}: {{ param.type }};
  {% endfor %}
}

export interface {{ endpoint.operation_id|title }}Response {
  // Define response structure based on API specification
  [key: string]: any;
}

{% endfor %}
{% endif %}

export class {{ class_name }}Error extends Error {
  public readonly status: number;
  public readonly response?: any;

  constructor(message: string, status: number, response?: any) {
    super(message);
    this.name = '{{ class_name }}Error';
    this.status = status;
    this.response = response;
  }
}

export class {{ class_name }} {
  private readonly baseUrl: string;
  {% if auth_type == 'api_key' %}
  private readonly apiKey: string;
  {% elif auth_type == 'bearer_token' %}
  private readonly token: string;
  {% endif %}
  private readonly defaultConfig: RequestConfig;

  {% if include_rate_limiting %}
  private rateLimitCalls: number = 0;
  private rateLimitReset: number = Date.now();
  private readonly rateLimitMax: number = 100;
  {% endif %}

  constructor(
    {% if auth_type == 'api_key' %}apiKey: string,{% elif auth_type == 'bearer_token' %}token: string,{% endif %}
    baseUrl: string = "{{ base_url }}",
    config: RequestConfig = {}
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    {% if auth_type == 'api_key' %}
    this.apiKey = apiKey;
    {% elif auth_type == 'bearer_token' %}
    this.token = token;
    {% endif %}
    this.defaultConfig = {
      timeout: 30000,
      retries: 3,
      ...config
    };
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': '{{ package_name }}/{{ version }}',
    };

    {% if auth_type == 'api_key' %}
    headers['X-API-Key'] = this.apiKey;
    {% elif auth_type == 'bearer_token' %}
    headers['Authorization'] = `Bearer ${this.token}`;
    {% endif %}

    return headers;
  }

  {% if include_rate_limiting %}
  private async checkRateLimit(): Promise<void> {
    if (this.rateLimitCalls >= this.rateLimitMax) {
      const waitTime = 60000 - (Date.now() - this.rateLimitReset);
      if (waitTime > 0) {
        await new Promise(resolve => setTimeout(resolve, waitTime));
        this.rateLimitCalls = 0;
        this.rateLimitReset = Date.now();
      }
    }
  }
  {% endif %}

  {% if include_retry_logic %}
  private async makeRequestWithRetry<T>(
    method: string,
    url: string,
    options: RequestInit,
    retries: number = this.defaultConfig.retries || 0
  ): Promise<T> {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.defaultConfig.timeout);

        const response = await fetch(url, {
          ...options,
          method,
          signal: controller.signal,
          headers: { ...this.getHeaders(), ...options.headers },
        });

        clearTimeout(timeoutId);

        if (response.status < 500) {
          if (!response.ok) {
            const errorText = await response.text();
            throw new {{ class_name }}Error(
              `API request failed: ${response.status} - ${errorText}`,
              response.status,
              errorText
            );
          }
          return await response.json();
        }

        if (attempt < retries) {
          await new Promise(resolve =>
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          );
        }
      } catch (error) {
        if (attempt < retries && !(error instanceof {{ class_name }}Error)) {
          await new Promise(resolve =>
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          );
          continue;
        }
        throw error;
      }
    }
    throw new {{ class_name }}Error('Max retries exceeded', 500);
  }
  {% endif %}

  private async makeRequest<T>(
    method: string,
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    {% if include_rate_limiting %}
    await this.checkRateLimit();
    {% endif %}

    {% if include_retry_logic %}
    const result = await this.makeRequestWithRetry<T>(method, url, options);
    {% else %}
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.defaultConfig.timeout);

    const response = await fetch(url, {
      ...options,
      method,
      signal: controller.signal,
      headers: { ...this.getHeaders(), ...options.headers },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new {{ class_name }}Error(
        `API request failed: ${response.status} - ${errorText}`,
        response.status,
        errorText
      );
    }

    const result = await response.json();
    {% endif %}

    {% if include_rate_limiting %}
    this.rateLimitCalls++;
    {% endif %}

    return result;
  }

{% for endpoint in endpoints %}
  /**
   * {{ endpoint.description or endpoint.summary or 'API endpoint' }}
   {% for param in endpoint.parameters %}
   * @param {{ param.name }}{% if not param.required %} (optional){% endif %} - {{ param.description or param.name }}
   {% endfor %}
   */
  public async {{ endpoint.method_name }}(
    {% if endpoint.parameters %}
    params: {{ endpoint.operation_id|title }}Request
    {% endif %}
  ): Promise<{{ endpoint.operation_id|title }}Response> {
    {% if endpoint.path_params %}
    let path = "{{ endpoint.path }}";
    {% for param in endpoint.path_params %}
    path = path.replace("{{{ param.name }}}", String(params.{{ param.name }}));
    {% endfor %}
    {% else %}
    const path = "{{ endpoint.path }}";
    {% endif %}

    const options: RequestInit = {};

    {% if endpoint.query_params %}
    const searchParams = new URLSearchParams();
    {% for param in endpoint.query_params %}
    if (params.{{ param.name }} !== undefined && params.{{ param.name }} !== null) {
      searchParams.append("{{ param.name }}", String(params.{{ param.name }}));
    }
    {% endfor %}
    const queryString = searchParams.toString();
    const finalPath = queryString ? `${path}?${queryString}` : path;
    {% else %}
    const finalPath = path;
    {% endif %}

    {% if endpoint.has_body %}
    const body: any = {};
    {% for param in endpoint.body_params %}
    if (params.{{ param.name }} !== undefined) {
      body.{{ param.name }} = params.{{ param.name }};
    }
    {% endfor %}
    options.body = JSON.stringify(body);
    {% endif %}

    return this.makeRequest<{{ endpoint.operation_id|title }}Response>(
      "{{ endpoint.method.upper() }}",
      finalPath,
      options
    );
  }

{% endfor %}
}

/**
 * Create a new {{ class_name }} instance
 */
export function createClient(
  {% if auth_type == 'api_key' %}apiKey: string,{% elif auth_type == 'bearer_token' %}token: string,{% endif %}
  baseUrl?: string,
  config?: RequestConfig
): {{ class_name }} {
  return new {{ class_name }}({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} baseUrl, config);
}

export default {{ class_name }};
'''

    def get_java_client_template(self) -> str:
        """Complete Java client template"""
        return '''package {{ package_name|replace('-', '') }};

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * {{ package_name }} - {{ description }}
 * Generated Java API client for {{ base_url }}
 */
public class {{ class_name }} {
    private final String baseUrl;
    {% if auth_type == 'api_key' %}
    private final String apiKey;
    {% elif auth_type == 'bearer_token' %}
    private final String token;
    {% endif %}
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    {% if include_rate_limiting %}
    private volatile int rateLimitCalls = 0;
    private volatile long rateLimitReset = System.currentTimeMillis();
    private static final int RATE_LIMIT_MAX = 100;
    {% endif %}

    /**
     * Create a new API client
     * @param {% if auth_type == 'api_key' %}apiKey Your API key{% elif auth_type == 'bearer_token' %}token Your bearer token{% endif %}
     * @param baseUrl Base URL for the API
     */
    public {{ class_name }}({% if auth_type == 'api_key' %}String apiKey,{% elif auth_type == 'bearer_token' %}String token,{% endif %} String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        {% if auth_type == 'api_key' %}
        this.apiKey = apiKey;
        {% elif auth_type == 'bearer_token' %}
        this.token = token;
        {% endif %}

        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(30))
                {% if include_retry_logic %}
                .build();
                {% else %}
                .build();
                {% endif %}

        this.objectMapper = new ObjectMapper();
    }

    /**
     * Default constructor with default base URL
     */
    public {{ class_name }}({% if auth_type == 'api_key' %}String apiKey{% elif auth_type == 'bearer_token' %}String token{% endif %}) {
        this({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} "{{ base_url }}");
    }

    private Map<String, String> getHeaders() {
        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "application/json");
        headers.put("User-Agent", "{{ package_name }}/{{ version }}");

        {% if auth_type == 'api_key' %}
        headers.put("X-API-Key", this.apiKey);
        {% elif auth_type == 'bearer_token' %}
        headers.put("Authorization", "Bearer " + this.token);
        {% endif %}

        return headers;
    }

    {% if include_rate_limiting %}
    private void checkRateLimit() throws InterruptedException {
        if (rateLimitCalls >= RATE_LIMIT_MAX) {
            long waitTime = 60000 - (System.currentTimeMillis() - rateLimitReset);
            if (waitTime > 0) {
                Thread.sleep(waitTime);
                rateLimitCalls = 0;
                rateLimitReset = System.currentTimeMillis();
            }
        }
    }
    {% endif %}

    {% if include_retry_logic %}
    private JsonNode makeRequestWithRetry(String method, String url, String body, int maxRetries)
            throws IOException, InterruptedException {
        IOException lastException = null;

        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .timeout(Duration.ofSeconds(30));

                // Add headers
                Map<String, String> headers = getHeaders();
                for (Map.Entry<String, String> header : headers.entrySet()) {
                    requestBuilder.header(header.getKey(), header.getValue());
                }

                // Set method and body
                switch (method.toUpperCase()) {
                    case "GET":
                        requestBuilder.GET();
                        break;
                    case "POST":
                        requestBuilder.POST(HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
                        break;
                    case "PUT":
                        requestBuilder.PUT(HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
                        break;
                    case "DELETE":
                        requestBuilder.DELETE();
                        break;
                    default:
                        requestBuilder.method(method, HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
                }

                HttpRequest request = requestBuilder.build();
                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() < 500) {
                    if (response.statusCode() >= 400) {
                        throw new {{ class_name }}Exception(
                                "API request failed: " + response.statusCode() + " - " + response.body(),
                                response.statusCode()
                        );
                    }
                    return objectMapper.readTree(response.body());
                }

                if (attempt < maxRetries) {
                    Thread.sleep((long) Math.pow(2, attempt) * 1000);
                }
            } catch (IOException | InterruptedException e) {
                lastException = e instanceof IOException ? (IOException) e : new IOException(e);
                if (attempt < maxRetries) {
                    Thread.sleep((long) Math.pow(2, attempt) * 1000);
                }
            }
        }

        throw lastException != null ? lastException : new IOException("Max retries exceeded");
    }
    {% endif %}

    private JsonNode makeRequest(String method, String endpoint, String body)
            throws IOException, InterruptedException {
        String url = this.baseUrl + endpoint;

        {% if include_rate_limiting %}
        checkRateLimit();
        {% endif %}

        {% if include_retry_logic %}
        JsonNode result = makeRequestWithRetry(method, url, body, 3);
        {% else %}
        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(30));

        // Add headers
        Map<String, String> headers = getHeaders();
        for (Map.Entry<String, String> header : headers.entrySet()) {
            requestBuilder.header(header.getKey(), header.getValue());
        }

        // Set method and body
        switch (method.toUpperCase()) {
            case "GET":
                requestBuilder.GET();
                break;
            case "POST":
                requestBuilder.POST(HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
                break;
            case "PUT":
                requestBuilder.PUT(HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
                break;
            case "DELETE":
                requestBuilder.DELETE();
                break;
            default:
                requestBuilder.method(method, HttpRequest.BodyPublishers.ofString(body != null ? body : ""));
        }

        HttpRequest request = requestBuilder.build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() >= 400) {
            throw new {{ class_name }}Exception(
                    "API request failed: " + response.statusCode() + " - " + response.body(),
                    response.statusCode()
            );
        }

        JsonNode result = objectMapper.readTree(response.body());
        {% endif %}

        {% if include_rate_limiting %}
        rateLimitCalls++;
        {% endif %}

        return result;
    }

{% for endpoint in endpoints %}
    /**
     * {{ endpoint.description or endpoint.summary or 'API endpoint' }}
     {% for param in endpoint.parameters %}
     * @param {{ param.name }} {{ param.description or param.name }}
     {% endfor %}
     * @return JsonNode response
     * @throws IOException if the request fails
     * @throws InterruptedException if the request is interrupted
     */
    public JsonNode {{ endpoint.method_name }}({% for param in endpoint.parameters %}{{ param.type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %})
            throws IOException, InterruptedException {

        {% if endpoint.path_params %}
        String path = "{{ endpoint.path }}";
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", String.valueOf({{ param.name }}));
        {% endfor %}
        {% else %}
        String path = "{{ endpoint.path }}";
        {% endif %}

        {% if endpoint.query_params %}
        StringBuilder queryParams = new StringBuilder();
        {% for param in endpoint.query_params %}
        if ({{ param.name }} != null) {
            if (queryParams.length() > 0) queryParams.append("&");
            queryParams.append("{{ param.name }}=").append({{ param.name }});
        }
        {% endfor %}

        if (queryParams.length() > 0) {
            path += "?" + queryParams.toString();
        }
        {% endif %}

        {% if endpoint.has_body %}
        Map<String, Object> body = new HashMap<>();
        {% for param in endpoint.body_params %}
        if ({{ param.name }} != null) {
            body.put("{{ param.name }}", {{ param.name }});
        }
        {% endfor %}

        String bodyJson = objectMapper.writeValueAsString(body);
        return makeRequest("{{ endpoint.method.upper() }}", path, bodyJson);
        {% else %}
        return makeRequest("{{ endpoint.method.upper() }}", path, null);
        {% endif %}
    }

{% endfor %}

    /**
     * Custom exception for API errors
     */
    public static class {{ class_name }}Exception extends RuntimeException {
        private final int statusCode;

        public {{ class_name }}Exception(String message, int statusCode) {
            super(message);
            this.statusCode = statusCode;
        }

        public int getStatusCode() {
            return statusCode;
        }
    }
}
'''

    def get_go_client_template(self) -> str:
        """Complete Go client template"""
        return '''// Package {{ package_name|replace('-', '') }} provides a Go client for {{ base_url }}
package {{ package_name|replace('-', '') }}

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// {{ class_name }} is the main API client
type {{ class_name }} struct {
	baseURL    string
	{% if auth_type == 'api_key' %}
	apiKey     string
	{% elif auth_type == 'bearer_token' %}
	token      string
	{% endif %}
	httpClient *http.Client

	{% if include_rate_limiting %}
	rateLimitCalls int
	rateLimitReset time.Time
	{% endif %}
}

// Config holds configuration options for the client
type Config struct {
	Timeout time.Duration
	{% if include_retry_logic %}
	MaxRetries int
	{% endif %}
}

// DefaultConfig returns default configuration
func DefaultConfig() *Config {
	return &Config{
		Timeout: 30 * time.Second,
		{% if include_retry_logic %}
		MaxRetries: 3,
		{% endif %}
	}
}

// {{ class_name }}Error represents an API error
type {{ class_name }}Error struct {
	StatusCode int
	Message    string
	Response   string
}

func (e *{{ class_name }}Error) Error() string {
	return fmt.Sprintf("API error %d: %s", e.StatusCode, e.Message)
}

// New{{ class_name }} creates a new API client
func New{{ class_name }}({% if auth_type == 'api_key' %}apiKey{% elif auth_type == 'bearer_token' %}token{% endif %} string, baseURL ...string) *{{ class_name }} {
	url := "{{ base_url }}"
	if len(baseURL) > 0 {
		url = baseURL[0]
	}

	return &{{ class_name }}{
		baseURL: strings.TrimSuffix(url, "/"),
		{% if auth_type == 'api_key' %}
		apiKey: apiKey,
		{% elif auth_type == 'bearer_token' %}
		token: token,
		{% endif %}
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		{% if include_rate_limiting %}
		rateLimitReset: time.Now(),
		{% endif %}
	}
}

// New{{ class_name }}WithConfig creates a new API client with custom configuration
func New{{ class_name }}WithConfig({% if auth_type == 'api_key' %}apiKey{% elif auth_type == 'bearer_token' %}token{% endif %} string, config *Config, baseURL ...string) *{{ class_name }} {
	client := New{{ class_name }}({% if auth_type == 'api_key' %}apiKey{% elif auth_type == 'bearer_token' %}token{% endif %}, baseURL...)
	client.httpClient.Timeout = config.Timeout
	return client
}

{% if include_rate_limiting %}
func (c *{{ class_name }}) checkRateLimit() {
	if c.rateLimitCalls >= 100 { // 100 calls per minute
		waitTime := 60*time.Second - time.Since(c.rateLimitReset)
		if waitTime > 0 {
			time.Sleep(waitTime)
			c.rateLimitCalls = 0
			c.rateLimitReset = time.Now()
		}
	}
}
{% endif %}

{% if include_retry_logic %}
func (c *{{ class_name }}) makeRequestWithRetry(ctx context.Context, method, endpoint string, body interface{}, maxRetries int) (map[string]interface{}, error) {
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		result, err := c.makeRequest(ctx, method, endpoint, body)

		if err == nil {
			return result, nil
		}

		// Check if it's a client error (4xx) - don't retry
		if apiErr, ok := err.(*{{ class_name }}Error); ok && apiErr.StatusCode < 500 {
			return nil, err
		}

		lastErr = err

		if attempt < maxRetries {
			backoff := time.Duration(attempt+1) * time.Second
			time.Sleep(backoff)
		}
	}

	return nil, lastErr
}
{% endif %}

func (c *{{ class_name }}) makeRequest(ctx context.Context, method, endpoint string, body interface{}) (map[string]interface{}, error) {
	url := c.baseURL + endpoint

	{% if include_rate_limiting %}
	c.checkRateLimit()
	{% endif %}

	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonBody)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "{{ package_name }}/{{ version }}")

	{% if auth_type == 'api_key' %}
	req.Header.Set("X-API-Key", c.apiKey)
	{% elif auth_type == 'bearer_token' %}
	req.Header.Set("Authorization", "Bearer "+c.token)
	{% endif %}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	{% if include_rate_limiting %}
	c.rateLimitCalls++
	{% endif %}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, &{{ class_name }}Error{
			StatusCode: resp.StatusCode,
			Message:    fmt.Sprintf("API request failed: %d", resp.StatusCode),
			Response:   string(respBody),
		}
	}

	var result map[string]interface{}
	if err := json.Unmarshal(respBody, &result); err != nil {
		// If not JSON, return the raw text
		return map[string]interface{}{"data": string(respBody)}, nil
	}

	return result, nil
}

{% for endpoint in endpoints %}
// {{ endpoint.method_name|title }} {{ endpoint.description or endpoint.summary or 'performs API call' }}
func (c *{{ class_name }}) {{ endpoint.method_name|title }}(ctx context.Context{% for param in endpoint.parameters %}, {{ param.name }} {{ param.type }}{% endfor %}) (map[string]interface{}, error) {
	{% if endpoint.path_params %}
	path := "{{ endpoint.path }}"
	{% for param in endpoint.path_params %}
	path = strings.ReplaceAll(path, "{{{ param.name }}}", fmt.Sprintf("%v", {{ param.name }}))
	{% endfor %}
	{% else %}
	path := "{{ endpoint.path }}"
	{% endif %}

	{% if endpoint.query_params %}
	params := url.Values{}
	{% for param in endpoint.query_params %}
	{% if param.type == "string" %}
	if {{ param.name }} != "" {
		params.Add("{{ param.name }}", {{ param.name }})
	}
	{% else %}
	if {{ param.name }} != {{ param.type }}(0) {
		params.Add("{{ param.name }}", fmt.Sprintf("%v", {{ param.name }}))
	}
	{% endif %}
	{% endfor %}

	if len(params) > 0 {
		path += "?" + params.Encode()
	}
	{% endif %}

	{% if endpoint.has_body %}
	body := map[string]interface{}{}
	{% for param in endpoint.body_params %}
	{% if param.type == "string" %}
	if {{ param.name }} != "" {
		body["{{ param.name }}"] = {{ param.name }}
	}
	{% else %}
	if {{ param.name }} != {{ param.type }}(0) {
		body["{{ param.name }}"] = {{ param.name }}
	}
	{% endif %}
	{% endfor %}

	{% if include_retry_logic %}
	return c.makeRequestWithRetry(ctx, "{{ endpoint.method.upper() }}", path, body, 3)
	{% else %}
	return c.makeRequest(ctx, "{{ endpoint.method.upper() }}", path, body)
	{% endif %}
	{% else %}
	{% if include_retry_logic %}
	return c.makeRequestWithRetry(ctx, "{{ endpoint.method.upper() }}", path, nil, 3)
	{% else %}
	return c.makeRequest(ctx, "{{ endpoint.method.upper() }}", path, nil)
	{% endif %}
	{% endif %}
}

{% endfor %}
'''

    def get_rust_client_template(self) -> str:
        """Complete Rust client template"""
        return '''//! {{ package_name }} - {{ description }}
//! Generated Rust API client for {{ base_url }}

use reqwest::{Client, Error as ReqwestError, Response};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum {{ class_name }}Error {
    #[error("HTTP request failed: {0}")]
    Request(#[from] ReqwestError),
    #[error("API error {status}: {message}")]
    Api { status: u16, message: String },
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Rate limit exceeded")]
    RateLimit,
}

pub type Result<T> = std::result::Result<T, {{ class_name }}Error>;

/// Configuration for the API client
#[derive(Debug, Clone)]
pub struct Config {
    pub timeout: Duration,
    {% if include_retry_logic %}
    pub max_retries: u32,
    pub retry_delay: Duration,
    {% endif %}
    {% if include_rate_limiting %}
    pub rate_limit: u32,
    {% endif %}
}

impl Default for Config {
    fn default() -> Self {
        Self {
            timeout: Duration::from_secs(30),
            {% if include_retry_logic %}
            max_retries: 3,
            retry_delay: Duration::from_secs(1),
            {% endif %}
            {% if include_rate_limiting %}
            rate_limit: 100,
            {% endif %}
        }
    }
}

/// Main API client
#[derive(Debug, Clone)]
pub struct {{ class_name }} {
    client: Client,
    base_url: String,
    {% if auth_type == 'api_key' %}
    api_key: String,
    {% elif auth_type == 'bearer_token' %}
    token: String,
    {% endif %}
    config: Config,
    {% if include_rate_limiting %}
    rate_limit_calls: std::sync::Arc<std::sync::Mutex<u32>>,
    rate_limit_reset: std::sync::Arc<std::sync::Mutex<Instant>>,
    {% endif %}
}

impl {{ class_name }} {
    /// Create a new API client
    pub fn new({% if auth_type == 'api_key' %}api_key: impl Into<String>{% elif auth_type == 'bearer_token' %}token: impl Into<String>{% endif %}) -> Result<Self> {
        Self::with_base_url({% if auth_type == 'api_key' %}api_key{% elif auth_type == 'bearer_token' %}token{% endif %}, "{{ base_url }}")
    }

    /// Create a new API client with custom base URL
    pub fn with_base_url(
        {% if auth_type == 'api_key' %}api_key: impl Into<String>,{% elif auth_type == 'bearer_token' %}token: impl Into<String>,{% endif %}
        base_url: impl Into<String>
    ) -> Result<Self> {
        Self::with_config({% if auth_type == 'api_key' %}api_key{% elif auth_type == 'bearer_token' %}token{% endif %}, base_url, Config::default())
    }

    /// Create a new API client with custom configuration
    pub fn with_config(
        {% if auth_type == 'api_key' %}api_key: impl Into<String>,{% elif auth_type == 'bearer_token' %}token: impl Into<String>,{% endif %}
        base_url: impl Into<String>,
        config: Config
    ) -> Result<Self> {
        let client = Client::builder()
            .timeout(config.timeout)
            .user_agent("{{ package_name }}/{{ version }}")
            .build()?;

        Ok(Self {
            client,
            base_url: base_url.into().trim_end_matches('/').to_string(),
            {% if auth_type == 'api_key' %}
            api_key: api_key.into(),
            {% elif auth_type == 'bearer_token' %}
            token: token.into(),
            {% endif %}
            config,
            {% if include_rate_limiting %}
            rate_limit_calls: std::sync::Arc::new(std::sync::Mutex::new(0)),
            rate_limit_reset: std::sync::Arc::new(std::sync::Mutex::new(Instant::now())),
            {% endif %}
        })
    }

    {% if include_rate_limiting %}
    async fn check_rate_limit(&self) -> Result<()> {
        let mut calls = self.rate_limit_calls.lock().unwrap();
        let mut reset = self.rate_limit_reset.lock().unwrap();

        if *calls >= self.config.rate_limit {
            let elapsed = reset.elapsed();
            if elapsed < Duration::from_secs(60) {
                let wait_time = Duration::from_secs(60) - elapsed;
                tokio::time::sleep(wait_time).await;
                *calls = 0;
                *reset = Instant::now();
            }
        }

        Ok(())
    }
    {% endif %}

    {% if include_retry_logic %}
    async fn make_request_with_retry(
        &self,
        method: reqwest::Method,
        url: String,
        body: Option<Value>
    ) -> Result<Value> {
        let mut last_error = None;

        for attempt in 0..=self.config.max_retries {
            match self.make_request_internal(method.clone(), url.clone(), body.clone()).await {
                Ok(response) => return Ok(response),
                Err(e) => {
                    // Don't retry client errors (4xx)
                    if let {{ class_name }}Error::Api { status, .. } = &e {
                        if *status < 500 {
                            return Err(e);
                        }
                    }

                    last_error = Some(e);

                    if attempt < self.config.max_retries {
                        let delay = self.config.retry_delay * (attempt + 1);
                        tokio::time::sleep(delay).await;
                    }
                }
            }
        }

        Err(last_error.unwrap())
    }
    {% endif %}

    async fn make_request_internal(
        &self,
        method: reqwest::Method,
        url: String,
        body: Option<Value>
    ) -> Result<Value> {
        {% if include_rate_limiting %}
        self.check_rate_limit().await?;
        {% endif %}

        let mut request = self.client.request(method, &url);

        // Add authentication headers
        {% if auth_type == 'api_key' %}
        request = request.header("X-API-Key", &self.api_key);
        {% elif auth_type == 'bearer_token' %}
        request = request.header("Authorization", format!("Bearer {}", self.token));
        {% endif %}

        // Add JSON body if provided
        if let Some(body) = body {
            request = request.json(&body);
        }

        let response = request.send().await?;

        {% if include_rate_limiting %}
        {
            let mut calls = self.rate_limit_calls.lock().unwrap();
            *calls += 1;
        }
        {% endif %}

        let status = response.status();
        let text = response.text().await?;

        if status.is_client_error() || status.is_server_error() {
            return Err({{ class_name }}Error::Api {
                status: status.as_u16(),
                message: text,
            });
        }

        // Try to parse as JSON, fallback to raw text
        match serde_json::from_str::<Value>(&text) {
            Ok(json) => Ok(json),
            Err(_) => Ok(serde_json::json!({"data": text})),
        }
    }

    async fn make_request(
        &self,
        method: reqwest::Method,
        endpoint: &str,
        body: Option<Value>
    ) -> Result<Value> {
        let url = format!("{}{}", self.base_url, endpoint);

        {% if include_retry_logic %}
        self.make_request_with_retry(method, url, body).await
        {% else %}
        self.make_request_internal(method, url, body).await
        {% endif %}
    }

{% for endpoint in endpoints %}
    /// {{ endpoint.description or endpoint.summary or 'API endpoint' }}
    pub async fn {{ endpoint.method_name }}(
        &self,
        {% for param in endpoint.parameters %}
        {{ param.name }}: {% if not param.required %}Option<{% endif %}{{ param.type }}{% if not param.required %}>{% endif %},
        {% endfor %}
    ) -> Result<Value> {
        {% if endpoint.path_params %}
        let mut path = "{{ endpoint.path }}".to_string();
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", &{{ param.name }}.to_string());
        {% endfor %}
        {% else %}
        let path = "{{ endpoint.path }}".to_string();
        {% endif %}

        {% if endpoint.query_params %}
        let mut query_params = Vec::new();
        {% for param in endpoint.query_params %}
        {% if param.required %}
        query_params.push(format!("{{ param.name }}={}", {{ param.name }}));
        {% else %}
        if let Some(val) = {{ param.name }} {
            query_params.push(format!("{{ param.name }}={}", val));
        }
        {% endif %}
        {% endfor %}

        let final_path = if query_params.is_empty() {
            path
        } else {
            format!("{}?{}", path, query_params.join("&"))
        };
        {% else %}
        let final_path = path;
        {% endif %}

        {% if endpoint.has_body %}
        let mut body = serde_json::Map::new();
        {% for param in endpoint.body_params %}
        {% if param.required %}
        body.insert("{{ param.name }}".to_string(), serde_json::to_value({{ param.name }})?);
        {% else %}
        if let Some(val) = {{ param.name }} {
            body.insert("{{ param.name }}".to_string(), serde_json::to_value(val)?);
        }
        {% endif %}
        {% endfor %}

        self.make_request(
            reqwest::Method::{{ endpoint.method.upper() }},
            &final_path,
            Some(Value::Object(body))
        ).await
        {% else %}
        self.make_request(
            reqwest::Method::{{ endpoint.method.upper() }},
            &final_path,
            None
        ).await
        {% endif %}
    }

{% endfor %}
}

{% if include_async_support %}
#[cfg(feature = "async")]
impl {{ class_name }} {
    // Async methods are already implemented above
}
{% endif %}
'''

    def get_swift_client_template(self) -> str:
        """Complete Swift client template"""
        return '''//
//  {{ class_name }}.swift
//  {{ package_name }}
//
//  Generated Swift API client for {{ base_url }}
//

import Foundation
{% if include_async_support %}
#if canImport(Combine)
import Combine
#endif
{% endif %}

/// API client error types
public enum {{ class_name }}Error: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError(Error)
    case networkError(Error)
    case httpError(statusCode: Int, data: Data?)
    case rateLimitExceeded

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .noData:
            return "No data received"
        case .decodingError(let error):
            return "Decoding error: \\(error.localizedDescription)"
        case .networkError(let error):
            return "Network error: \\(error.localizedDescription)"
        case .httpError(let statusCode, _):
            return "HTTP error: \\(statusCode)"
        case .rateLimitExceeded:
            return "Rate limit exceeded"
        }
    }
}

/// Configuration for the API client
public struct {{ class_name }}Config {
    public let timeout: TimeInterval
    {% if include_retry_logic %}
    public let maxRetries: Int
    public let retryDelay: TimeInterval
    {% endif %}
    {% if include_rate_limiting %}
    public let rateLimit: Int
    {% endif %}

    public init(
        timeout: TimeInterval = 30,
        {% if include_retry_logic %}
        maxRetries: Int = 3,
        retryDelay: TimeInterval = 1,
        {% endif %}
        {% if include_rate_limiting %}
        rateLimit: Int = 100
        {% endif %}
    ) {
        self.timeout = timeout
        {% if include_retry_logic %}
        self.maxRetries = maxRetries
        self.retryDelay = retryDelay
        {% endif %}
        {% if include_rate_limiting %}
        self.rateLimit = rateLimit
        {% endif %}
    }
}

/// Main API client
public class {{ class_name }} {
    private let baseURL: String
    {% if auth_type == 'api_key' %}
    private let apiKey: String
    {% elif auth_type == 'bearer_token' %}
    private let token: String
    {% endif %}
    private let session: URLSession
    private let config: {{ class_name }}Config

    {% if include_rate_limiting %}
    private var rateLimitCalls: Int = 0
    private var rateLimitReset: Date = Date()
    private let rateLimitQueue = DispatchQueue(label: "{{ package_name }}.ratelimit")
    {% endif %}

    /// Initialize the API client
    /// - Parameters:
    ///   - {% if auth_type == 'api_key' %}apiKey: Your API key{% elif auth_type == 'bearer_token' %}token: Your bearer token{% endif %}
    ///   - baseURL: Base URL for the API (optional)
    ///   - config: Client configuration (optional)
    public init(
        {% if auth_type == 'api_key' %}apiKey: String,{% elif auth_type == 'bearer_token' %}token: String,{% endif %}
        baseURL: String = "{{ base_url }}",
        config: {{ class_name }}Config = {{ class_name }}Config()
    ) {
        self.baseURL = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        {% if auth_type == 'api_key' %}
        self.apiKey = apiKey
        {% elif auth_type == 'bearer_token' %}
        self.token = token
        {% endif %}
        self.config = config

        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = config.timeout
        configuration.timeoutIntervalForResource = config.timeout
        self.session = URLSession(configuration: configuration)
    }

    private func createHeaders() -> [String: String] {
        var headers = [
            "Content-Type": "application/json",
            "User-Agent": "{{ package_name }}/{{ version }}"
        ]

        {% if auth_type == 'api_key' %}
        headers["X-API-Key"] = apiKey
        {% elif auth_type == 'bearer_token' %}
        headers["Authorization"] = "Bearer \\(token)"
        {% endif %}

        return headers
    }

    {% if include_rate_limiting %}
    private func checkRateLimit() async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            rateLimitQueue.async {
                if self.rateLimitCalls >= self.config.rateLimit {
                    let elapsed = Date().timeIntervalSince(self.rateLimitReset)
                    if elapsed < 60 {
                        let waitTime = 60 - elapsed
                        DispatchQueue.main.asyncAfter(deadline: .now() + waitTime) {
                            self.rateLimitCalls = 0
                            self.rateLimitReset = Date()
                            continuation.resume()
                        }
                        return
                    }
                }
                continuation.resume()
            }
        }
    }
    {% endif %}

    {% if include_retry_logic %}
    private func makeRequestWithRetry<T: Codable>(
        method: HTTPMethod,
        endpoint: String,
        body: [String: Any]? = nil,
        responseType: T.Type
    ) async throws -> T {
        var lastError: Error?

        for attempt in 0...config.maxRetries {
            do {
                return try await makeRequestInternal(
                    method: method,
                    endpoint: endpoint,
                    body: body,
                    responseType: responseType
                )
            } catch let error as {{ class_name }}Error {
                // Don't retry client errors (4xx)
                if case .httpError(let statusCode, _) = error, statusCode < 500 {
                    throw error
                }
                lastError = error

                if attempt < config.maxRetries {
                    try await Task.sleep(nanoseconds: UInt64(config.retryDelay * Double(attempt + 1) * 1_000_000_000))
                }
            } catch {
                lastError = error
                if attempt < config.maxRetries {
                    try await Task.sleep(nanoseconds: UInt64(config.retryDelay * Double(attempt + 1) * 1_000_000_000))
                }
            }
        }

        throw lastError ?? {{ class_name }}Error.networkError(NSError(domain: "Unknown", code: -1))
    }
    {% endif %}

    private func makeRequestInternal<T: Codable>(
        method: HTTPMethod,
        endpoint: String,
        body: [String: Any]? = nil,
        responseType: T.Type
    ) async throws -> T {
        {% if include_rate_limiting %}
        try await checkRateLimit()
        {% endif %}

        guard let url = URL(string: "\\(baseURL)\\(endpoint)") else {
            throw {{ class_name }}Error.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue

        // Add headers
        for (key, value) in createHeaders() {
            request.setValue(value, forHTTPHeaderField: key)
        }

        // Add body if provided
        if let body = body {
            do {
                request.httpBody = try JSONSerialization.data(withJSONObject: body)
            } catch {
                throw {{ class_name }}Error.decodingError(error)
            }
        }

        do {
            let (data, response) = try await session.data(for: request)

            {% if include_rate_limiting %}
            rateLimitQueue.async {
                self.rateLimitCalls += 1
            }
            {% endif %}

            guard let httpResponse = response as? HTTPURLResponse else {
                throw {{ class_name }}Error.networkError(NSError(domain: "Invalid response", code: -1))
            }

            guard 200...299 ~= httpResponse.statusCode else {
                throw {{ class_name }}Error.httpError(statusCode: httpResponse.statusCode, data: data)
            }

            guard !data.isEmpty else {
                throw {{ class_name }}Error.noData
            }

            do {
                let result = try JSONDecoder().decode(responseType, from: data)
                return result
            } catch {
                throw {{ class_name }}Error.decodingError(error)
            }
        } catch {
            throw {{ class_name }}Error.networkError(error)
        }
    }

    private func makeRequest<T: Codable>(
        method: HTTPMethod,
        endpoint: String,
        body: [String: Any]? = nil,
        responseType: T.Type
    ) async throws -> T {
        {% if include_retry_logic %}
        return try await makeRequestWithRetry(
            method: method,
            endpoint: endpoint,
            body: body,
            responseType: responseType
        )
        {% else %}
        return try await makeRequestInternal(
            method: method,
            endpoint: endpoint,
            body: body,
            responseType: responseType
        )
        {% endif %}
    }
}

/// HTTP methods
private enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
    case PATCH = "PATCH"
}

// MARK: - API Methods
extension {{ class_name }} {
{% for endpoint in endpoints %}
    /// {{ endpoint.description or endpoint.summary or 'API endpoint' }}
    /// - Parameters:
    {% for param in endpoint.parameters %}
    ///   - {{ param.name }}: {{ param.description or param.name }}
    {% endfor %}
    /// - Returns: API response
    public func {{ endpoint.method_name }}(
        {% for param in endpoint.parameters %}
        {{ param.name }}: {{ param.type }}{% if not param.required %}?{% endif %}{% if not loop.last %},{% endif %}
        {% endfor %}
    ) async throws -> [String: Any] {
        {% if endpoint.path_params %}
        var path = "{{ endpoint.path }}"
        {% for param in endpoint.path_params %}
        path = path.replacingOccurrences(of: "{{{ param.name }}}", with: String({{ param.name }}))
        {% endfor %}
        {% else %}
        let path = "{{ endpoint.path }}"
        {% endif %}

        {% if endpoint.query_params %}
        var queryItems: [URLQueryItem] = []
        {% for param in endpoint.query_params %}
        {% if param.required %}
        queryItems.append(URLQueryItem(name: "{{ param.name }}", value: String({{ param.name }})))
        {% else %}
        if let {{ param.name }} = {{ param.name }} {
            queryItems.append(URLQueryItem(name: "{{ param.name }}", value: String({{ param.name }})))
        }
        {% endif %}
        {% endfor %}

        var components = URLComponents(string: path)
        if !queryItems.isEmpty {
            components?.queryItems = queryItems
        }
        let finalPath = components?.string ?? path
        {% else %}
        let finalPath = path
        {% endif %}

        {% if endpoint.has_body %}
        var body: [String: Any] = [:]
        {% for param in endpoint.body_params %}
        {% if param.required %}
        body["{{ param.name }}"] = {{ param.name }}
        {% else %}
        if let {{ param.name }} = {{ param.name }} {
            body["{{ param.name }}"] = {{ param.name }}
        }
        {% endif %}
        {% endfor %}

        return try await makeRequest(
            method: .{{ endpoint.method.upper() }},
            endpoint: finalPath,
            body: body,
            responseType: [String: Any].self
        )
        {% else %}
        return try await makeRequest(
            method: .{{ endpoint.method.upper() }},
            endpoint: finalPath,
            responseType: [String: Any].self
        )
        {% endif %}
    }

{% endfor %}
}

{% if include_async_support %}
#if canImport(Combine)
// MARK: - Combine Support
@available(iOS 13.0, macOS 10.15, tvOS 13.0, watchOS 6.0, *)
extension {{ class_name }} {
{% for endpoint in endpoints %}
    /// {{ endpoint.description or endpoint.summary or 'API endpoint' }} (Combine version)
    public func {{ endpoint.method_name }}Publisher(
        {% for param in endpoint.parameters %}
        {{ param.name }}: {{ param.type }}{% if not param.required %}?{% endif %}{% if not loop.last %},{% endif %}
        {% endfor %}
    ) -> AnyPublisher<[String: Any], {{ class_name }}Error> {
        return Future { promise in
            Task {
                do {
                    let result = try await self.{{ endpoint.method_name }}(
                        {% for param in endpoint.parameters %}
                        {{ param.name }}: {{ param.name }}{% if not loop.last %},{% endif %}
                        {% endfor %}
                    )
                    promise(.success(result))
                } catch {
                    if let apiError = error as? {{ class_name }}Error {
                        promise(.failure(apiError))
                    } else {
                        promise(.failure(.networkError(error)))
                    }
                }
            }
        }
        .eraseToAnyPublisher()
    }

{% endfor %}
}
#endif
{% endif %}
'''