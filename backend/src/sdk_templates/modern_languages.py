#!/usr/bin/env python3
"""
Modern Language Templates for SDK Generation
Support for Kotlin, Dart/Flutter, C#, PHP, Ruby, and Scala
"""


class ModernLanguageTemplates:
    """Templates for modern programming languages"""

    def get_kotlin_client_template(self) -> str:
        """Complete Kotlin client template"""
        return """package {{ package_name|replace('-', '.') }}

import kotlinx.coroutines.*
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.features.*
import io.ktor.client.features.json.*
import io.ktor.client.features.json.serializer.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import java.time.Instant
import kotlin.time.Duration.Companion.seconds

/**
 * {{ package_name }} - {{ description }}
 * Generated Kotlin API client for {{ base_url }}
 */

@Serializable
data class ApiResponse<T>(
    val data: T? = null,
    val error: String? = null,
    val status: Int = 200
)

class {{ class_name }}Exception(
    message: String,
    val statusCode: Int = 0,
    cause: Throwable? = null
) : Exception(message, cause)

data class {{ class_name }}Config(
    val timeout: kotlin.time.Duration = 30.seconds,
    {% if include_retry_logic %}
    val maxRetries: Int = 3,
    val retryDelay: kotlin.time.Duration = 1.seconds,
    {% endif %}
    {% if include_rate_limiting %}
    val rateLimit: Int = 100
    {% endif %}
)

class {{ class_name }}(
    {% if auth_type == 'api_key' %}
    private val apiKey: String,
    {% elif auth_type == 'bearer_token' %}
    private val token: String,
    {% endif %}
    private val baseUrl: String = "{{ base_url }}",
    private val config: {{ class_name }}Config = {{ class_name }}Config()
) {
    private val httpClient = HttpClient(CIO) {
        install(JsonFeature) {
            serializer = KotlinxSerializer(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }

        install(HttpTimeout) {
            requestTimeoutMillis = config.timeout.inWholeMilliseconds
            connectTimeoutMillis = config.timeout.inWholeMilliseconds
        }

        defaultRequest {
            header("Content-Type", "application/json")
            header("User-Agent", "{{ package_name }}/{{ version }}")
            {% if auth_type == 'api_key' %}
            header("X-API-Key", apiKey)
            {% elif auth_type == 'bearer_token' %}
            header("Authorization", "Bearer $token")
            {% endif %}
        }
    }

    {% if include_rate_limiting %}
    private var rateLimitCalls = 0
    private var rateLimitReset = Instant.now()

    private suspend fun checkRateLimit() {
        if (rateLimitCalls >= config.rateLimit) {
            val elapsed = java.time.Duration.between(rateLimitReset, Instant.now())
            if (elapsed.toMillis() < 60000) {
                val waitTime = 60000 - elapsed.toMillis()
                delay(waitTime)
                rateLimitCalls = 0
                rateLimitReset = Instant.now()
            }
        }
    }
    {% endif %}

    {% if include_retry_logic %}
    private suspend fun <T> makeRequestWithRetry(
        block: suspend () -> T
    ): T {
        var lastException: Exception? = null

        repeat(config.maxRetries + 1) { attempt ->
            try {
                return block()
            } catch (e: {{ class_name }}Exception) {
                // Don't retry client errors (4xx)
                if (e.statusCode in 400..499) {
                    throw e
                }
                lastException = e

                if (attempt < config.maxRetries) {
                    delay(config.retryDelay.inWholeMilliseconds * (attempt + 1))
                }
            } catch (e: Exception) {
                lastException = e

                if (attempt < config.maxRetries) {
                    delay(config.retryDelay.inWholeMilliseconds * (attempt + 1))
                }
            }
        }

        throw lastException ?: {{ class_name }}Exception("Max retries exceeded")
    }
    {% endif %}

    private suspend inline fun <reified T> makeRequest(
        method: HttpMethod,
        endpoint: String,
        body: Any? = null
    ): T {
        {% if include_rate_limiting %}
        checkRateLimit()
        {% endif %}

        val url = "$baseUrl$endpoint"

        {% if include_retry_logic %}
        return makeRequestWithRetry {
        {% endif %}
            val response: HttpResponse = httpClient.request(url) {
                this.method = method
                if (body != null) {
                    setBody(body)
                }
            }

            {% if include_rate_limiting %}
            rateLimitCalls++
            {% endif %}

            if (response.status.value >= 400) {
                val errorBody = response.bodyAsText()
                throw {{ class_name }}Exception(
                    "API request failed: ${response.status.value} - $errorBody",
                    response.status.value
                )
            }

            response.body()
        {% if include_retry_logic %}
        }
        {% endif %}
    }

{% for endpoint in endpoints %}
    /**
     * {{ endpoint.description or endpoint.summary or 'API endpoint' }}
     {% for param in endpoint.parameters %}
     * @param {{ param.name }} {{ param.description or param.name }}
     {% endfor %}
     */
    suspend fun {{ endpoint.method_name }}(
        {% for param in endpoint.parameters %}
        {{ param.name }}: {{ param.type }}{% if not param.required %}?{% endif %}{% if not loop.last %},{% endif %}
        {% endfor %}
    ): Map<String, Any> {
        {% if endpoint.path_params %}
        var path = "{{ endpoint.path }}"
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", {{ param.name }}.toString())
        {% endfor %}
        {% else %}
        val path = "{{ endpoint.path }}"
        {% endif %}

        {% if endpoint.query_params %}
        val queryParams = mutableListOf<String>()
        {% for param in endpoint.query_params %}
        {% if param.required %}
        queryParams.add("{{ param.name }}=${{ param.name }}")
        {% else %}
        {{ param.name }}?.let { queryParams.add("{{ param.name }}=$it") }
        {% endif %}
        {% endfor %}

        val finalPath = if (queryParams.isNotEmpty()) {
            "$path?${queryParams.joinToString("&")}"
        } else {
            path
        }
        {% else %}
        val finalPath = path
        {% endif %}

        {% if endpoint.has_body %}
        val body = buildMap {
            {% for param in endpoint.body_params %}
            {% if param.required %}
            put("{{ param.name }}", {{ param.name }})
            {% else %}
            {{ param.name }}?.let { put("{{ param.name }}", it) }
            {% endif %}
            {% endfor %}
        }

        return makeRequest(HttpMethod.{{ endpoint.method.title() }}, finalPath, body)
        {% else %}
        return makeRequest(HttpMethod.{{ endpoint.method.title() }}, finalPath)
        {% endif %}
    }

{% endfor %}

    fun close() {
        httpClient.close()
    }
}

/**
 * Create a new {{ class_name }} instance
 */
fun create{{ class_name }}(
    {% if auth_type == 'api_key' %}apiKey: String,{% elif auth_type == 'bearer_token' %}token: String,{% endif %}
    baseUrl: String = "{{ base_url }}",
    config: {{ class_name }}Config = {{ class_name }}Config()
): {{ class_name }} {
    return {{ class_name }}({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} baseUrl, config)
}
"""

    def get_dart_client_template(self) -> str:
        """Complete Dart/Flutter client template"""
        return """/// {{ package_name }} - {{ description }}
/// Generated Dart API client for {{ base_url }}

library {{ package_name|replace('-', '_') }};

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// Exception thrown by the API client
class {{ class_name }}Exception implements Exception {
  final String message;
  final int? statusCode;
  final dynamic response;

  const {{ class_name }}Exception(this.message, [this.statusCode, this.response]);

  @override
  String toString() => '{{ class_name }}Exception: $message';
}

/// Configuration for the API client
class {{ class_name }}Config {
  final Duration timeout;
  {% if include_retry_logic %}
  final int maxRetries;
  final Duration retryDelay;
  {% endif %}
  {% if include_rate_limiting %}
  final int rateLimit;
  {% endif %}

  const {{ class_name }}Config({
    this.timeout = const Duration(seconds: 30),
    {% if include_retry_logic %}
    this.maxRetries = 3,
    this.retryDelay = const Duration(seconds: 1),
    {% endif %}
    {% if include_rate_limiting %}
    this.rateLimit = 100,
    {% endif %}
  });
}

/// Main API client
class {{ class_name }} {
  final String _baseUrl;
  {% if auth_type == 'api_key' %}
  final String _apiKey;
  {% elif auth_type == 'bearer_token' %}
  final String _token;
  {% endif %}
  final http.Client _httpClient;
  final {{ class_name }}Config _config;

  {% if include_rate_limiting %}
  int _rateLimitCalls = 0;
  DateTime _rateLimitReset = DateTime.now();
  {% endif %}

  /// Create a new API client
  {{ class_name }}({
    {% if auth_type == 'api_key' %}
    required String apiKey,
    {% elif auth_type == 'bearer_token' %}
    required String token,
    {% endif %}
    String baseUrl = '{{ base_url }}',
    {{ class_name }}Config config = const {{ class_name }}Config(),
    http.Client? httpClient,
  })  : _baseUrl = baseUrl.replaceAll(RegExp(r'/$'), ''),
        {% if auth_type == 'api_key' %}
        _apiKey = apiKey,
        {% elif auth_type == 'bearer_token' %}
        _token = token,
        {% endif %}
        _httpClient = httpClient ?? http.Client(),
        _config = config;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'User-Agent': '{{ package_name }}/{{ version }}',
        {% if auth_type == 'api_key' %}
        'X-API-Key': _apiKey,
        {% elif auth_type == 'bearer_token' %}
        'Authorization': 'Bearer $_token',
        {% endif %}
      };

  {% if include_rate_limiting %}
  Future<void> _checkRateLimit() async {
    if (_rateLimitCalls >= _config.rateLimit) {
      final elapsed = DateTime.now().difference(_rateLimitReset);
      if (elapsed.inMilliseconds < 60000) {
        final waitTime = 60000 - elapsed.inMilliseconds;
        await Future.delayed(Duration(milliseconds: waitTime));
        _rateLimitCalls = 0;
        _rateLimitReset = DateTime.now();
      }
    }
  }
  {% endif %}

  {% if include_retry_logic %}
  Future<T> _makeRequestWithRetry<T>(
    Future<T> Function() request,
  ) async {
    Exception? lastException;

    for (int attempt = 0; attempt <= _config.maxRetries; attempt++) {
      try {
        return await request();
      } on {{ class_name }}Exception catch (e) {
        // Don't retry client errors (4xx)
        if (e.statusCode != null && e.statusCode! >= 400 && e.statusCode! < 500) {
          rethrow;
        }
        lastException = e;

        if (attempt < _config.maxRetries) {
          await Future.delayed(_config.retryDelay * (attempt + 1));
        }
      } catch (e) {
        lastException = e is Exception ? e : Exception(e.toString());

        if (attempt < _config.maxRetries) {
          await Future.delayed(_config.retryDelay * (attempt + 1));
        }
      }
    }

    throw lastException ?? const {{ class_name }}Exception('Max retries exceeded');
  }
  {% endif %}

  Future<Map<String, dynamic>> _makeRequest(
    String method,
    String endpoint, {
    Map<String, dynamic>? body,
    Map<String, String>? queryParams,
  }) async {
    {% if include_rate_limiting %}
    await _checkRateLimit();
    {% endif %}

    var url = '$_baseUrl$endpoint';
    if (queryParams != null && queryParams.isNotEmpty) {
      final query = queryParams.entries
          .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
          .join('&');
      url += '?$query';
    }

    {% if include_retry_logic %}
    return await _makeRequestWithRetry(() async {
    {% endif %}
      final uri = Uri.parse(url);
      late final http.Response response;

      switch (method.toUpperCase()) {
        case 'GET':
          response = await _httpClient
              .get(uri, headers: _headers)
              .timeout(_config.timeout);
          break;
        case 'POST':
          response = await _httpClient
              .post(
                uri,
                headers: _headers,
                body: body != null ? jsonEncode(body) : null,
              )
              .timeout(_config.timeout);
          break;
        case 'PUT':
          response = await _httpClient
              .put(
                uri,
                headers: _headers,
                body: body != null ? jsonEncode(body) : null,
              )
              .timeout(_config.timeout);
          break;
        case 'DELETE':
          response = await _httpClient
              .delete(uri, headers: _headers)
              .timeout(_config.timeout);
          break;
        default:
          throw {{ class_name }}Exception('Unsupported HTTP method: $method');
      }

      {% if include_rate_limiting %}
      _rateLimitCalls++;
      {% endif %}

      if (response.statusCode >= 400) {
        throw {{ class_name }}Exception(
          'API request failed: ${response.statusCode} - ${response.body}',
          response.statusCode,
          response.body,
        );
      }

      try {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } catch (e) {
        return {'data': response.body};
      }
    {% if include_retry_logic %}
    });
    {% endif %}
  }

{% for endpoint in endpoints %}
  /// {{ endpoint.description or endpoint.summary or 'API endpoint' }}
  ///
  /// Parameters:
  {% for param in endpoint.parameters %}
  /// - [{{ param.name }}]: {{ param.description or param.name }}
  {% endfor %}
  Future<Map<String, dynamic>> {{ endpoint.method_name }}({
    {% for param in endpoint.parameters %}
    {% if param.required %}required {% endif %}{{ param.type }}{% if not param.required %}?{% endif %} {{ param.name }},
    {% endfor %}
  }) async {
    {% if endpoint.path_params %}
    var path = '{{ endpoint.path }}';
    {% for param in endpoint.path_params %}
    path = path.replaceAll('{{{ param.name }}}', {{ param.name }}.toString());
    {% endfor %}
    {% else %}
    const path = '{{ endpoint.path }}';
    {% endif %}

    {% if endpoint.query_params %}
    final queryParams = <String, String>{};
    {% for param in endpoint.query_params %}
    {% if param.required %}
    queryParams['{{ param.name }}'] = {{ param.name }}.toString();
    {% else %}
    if ({{ param.name }} != null) {
      queryParams['{{ param.name }}'] = {{ param.name }}!.toString();
    }
    {% endif %}
    {% endfor %}
    {% endif %}

    {% if endpoint.has_body %}
    final body = <String, dynamic>{};
    {% for param in endpoint.body_params %}
    {% if param.required %}
    body['{{ param.name }}'] = {{ param.name }};
    {% else %}
    if ({{ param.name }} != null) {
      body['{{ param.name }}'] = {{ param.name }};
    }
    {% endif %}
    {% endfor %}
    {% endif %}

    return _makeRequest(
      '{{ endpoint.method.upper() }}',
      path,
      {% if endpoint.has_body %}
      body: body,
      {% endif %}
      {% if endpoint.query_params %}
      queryParams: queryParams,
      {% endif %}
    );
  }

{% endfor %}

  /// Close the HTTP client
  void close() {
    _httpClient.close();
  }
}

/// Create a new {{ class_name }} instance
{{ class_name }} create{{ class_name }}({
  {% if auth_type == 'api_key' %}
  required String apiKey,
  {% elif auth_type == 'bearer_token' %}
  required String token,
  {% endif %}
  String baseUrl = '{{ base_url }}',
  {{ class_name }}Config config = const {{ class_name }}Config(),
}) {
  return {{ class_name }}(
    {% if auth_type == 'api_key' %}
    apiKey: apiKey,
    {% elif auth_type == 'bearer_token' %}
    token: token,
    {% endif %}
    baseUrl: baseUrl,
    config: config,
  );
}
"""

    def get_csharp_client_template(self) -> str:
        """Complete C# client template"""
        return """using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Web;

namespace {{ package_name|replace('-', '.') |title }}
{
    /// <summary>
    /// {{ package_name }} - {{ description }}
    /// Generated C# API client for {{ base_url }}
    /// </summary>
    public class {{ class_name }}Exception : Exception
    {
        public int StatusCode { get; }
        public string? ResponseBody { get; }

        public {{ class_name }}Exception(string message, int statusCode = 0, string? responseBody = null)
            : base(message)
        {
            StatusCode = statusCode;
            ResponseBody = responseBody;
        }
    }

    public class {{ class_name }}Config
    {
        public TimeSpan Timeout { get; set; } = TimeSpan.FromSeconds(30);
        {% if include_retry_logic %}
        public int MaxRetries { get; set; } = 3;
        public TimeSpan RetryDelay { get; set; } = TimeSpan.FromSeconds(1);
        {% endif %}
        {% if include_rate_limiting %}
        public int RateLimit { get; set; } = 100;
        {% endif %}
    }

    public class {{ class_name }} : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        {% if auth_type == 'api_key' %}
        private readonly string _apiKey;
        {% elif auth_type == 'bearer_token' %}
        private readonly string _token;
        {% endif %}
        private readonly {{ class_name }}Config _config;

        {% if include_rate_limiting %}
        private int _rateLimitCalls = 0;
        private DateTime _rateLimitReset = DateTime.Now;
        private readonly object _rateLimitLock = new object();
        {% endif %}

        /// <summary>
        /// Initialize the API client
        /// </summary>
        /// <param name="{% if auth_type == 'api_key' %}apiKey">Your API key{% elif auth_type == 'bearer_token' %}token">Your bearer token{% endif %}</param>
        /// <param name="baseUrl">Base URL for the API</param>
        /// <param name="config">Client configuration</param>
        /// <param name="httpClient">Custom HTTP client (optional)</param>
        public {{ class_name }}(
            {% if auth_type == 'api_key' %}
            string apiKey,
            {% elif auth_type == 'bearer_token' %}
            string token,
            {% endif %}
            string baseUrl = "{{ base_url }}",
            {{ class_name }}Config? config = null,
            HttpClient? httpClient = null)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            {% if auth_type == 'api_key' %}
            _apiKey = apiKey ?? throw new ArgumentNullException(nameof(apiKey));
            {% elif auth_type == 'bearer_token' %}
            _token = token ?? throw new ArgumentNullException(nameof(token));
            {% endif %}
            _config = config ?? new {{ class_name }}Config();

            _httpClient = httpClient ?? new HttpClient();
            _httpClient.Timeout = _config.Timeout;

            SetupDefaultHeaders();
        }

        private void SetupDefaultHeaders()
        {
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "{{ package_name }}/{{ version }}");

            {% if auth_type == 'api_key' %}
            _httpClient.DefaultRequestHeaders.Add("X-API-Key", _apiKey);
            {% elif auth_type == 'bearer_token' %}
            _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {_token}");
            {% endif %}
        }

        {% if include_rate_limiting %}
        private async Task CheckRateLimitAsync()
        {
            lock (_rateLimitLock)
            {
                if (_rateLimitCalls >= _config.RateLimit)
                {
                    var elapsed = DateTime.Now - _rateLimitReset;
                    if (elapsed.TotalMilliseconds < 60000)
                    {
                        var waitTime = TimeSpan.FromMilliseconds(60000 - elapsed.TotalMilliseconds);
                        Task.Delay(waitTime).Wait();
                        _rateLimitCalls = 0;
                        _rateLimitReset = DateTime.Now;
                    }
                }
            }
        }
        {% endif %}

        {% if include_retry_logic %}
        private async Task<T> MakeRequestWithRetryAsync<T>(Func<Task<T>> request)
        {
            Exception? lastException = null;

            for (int attempt = 0; attempt <= _config.MaxRetries; attempt++)
            {
                try
                {
                    return await request();
                }
                catch ({{ class_name }}Exception ex) when (ex.StatusCode >= 400 && ex.StatusCode < 500)
                {
                    // Don't retry client errors (4xx)
                    throw;
                }
                catch (Exception ex)
                {
                    lastException = ex;

                    if (attempt < _config.MaxRetries)
                    {
                        var delay = TimeSpan.FromMilliseconds(_config.RetryDelay.TotalMilliseconds * (attempt + 1));
                        await Task.Delay(delay);
                    }
                }
            }

            throw lastException ?? new {{ class_name }}Exception("Max retries exceeded");
        }
        {% endif %}

        private async Task<Dictionary<string, object>> MakeRequestAsync(
            HttpMethod method,
            string endpoint,
            object? body = null,
            CancellationToken cancellationToken = default)
        {
            {% if include_rate_limiting %}
            await CheckRateLimitAsync();
            {% endif %}

            var url = $"{_baseUrl}{endpoint}";

            {% if include_retry_logic %}
            return await MakeRequestWithRetryAsync(async () =>
            {
            {% endif %}
                using var request = new HttpRequestMessage(method, url);

                if (body != null)
                {
                    var json = JsonSerializer.Serialize(body);
                    request.Content = new StringContent(json, Encoding.UTF8, "application/json");
                }

                using var response = await _httpClient.SendAsync(request, cancellationToken);

                {% if include_rate_limiting %}
                lock (_rateLimitLock)
                {
                    _rateLimitCalls++;
                }
                {% endif %}

                var content = await response.Content.ReadAsStringAsync(cancellationToken);

                if (!response.IsSuccessStatusCode)
                {
                    throw new {{ class_name }}Exception(
                        $"API request failed: {(int)response.StatusCode} - {content}",
                        (int)response.StatusCode,
                        content);
                }

                try
                {
                    return JsonSerializer.Deserialize<Dictionary<string, object>>(content) ??
                           new Dictionary<string, object>();
                }
                catch (JsonException)
                {
                    return new Dictionary<string, object> { ["data"] = content };
                }
            {% if include_retry_logic %}
            });
            {% endif %}
        }

{% for endpoint in endpoints %}
        /// <summary>
        /// {{ endpoint.description or endpoint.summary or 'API endpoint' }}
        /// </summary>
        {% for param in endpoint.parameters %}
        /// <param name="{{ param.name }}">{{ param.description or param.name }}</param>
        {% endfor %}
        /// <param name="cancellationToken">Cancellation token</param>
        /// <returns>API response</returns>
        public async Task<Dictionary<string, object>> {{ endpoint.method_name|title }}Async(
            {% for param in endpoint.parameters %}
            {{ param.type }}{% if not param.required %}?{% endif %} {{ param.name }}{% if not param.required %} = null{% endif %},
            {% endfor %}
            CancellationToken cancellationToken = default)
        {
            {% if endpoint.path_params %}
            var path = "{{ endpoint.path }}";
            {% for param in endpoint.path_params %}
            path = path.Replace("{{{ param.name }}}", {{ param.name }}?.ToString() ?? "");
            {% endfor %}
            {% else %}
            var path = "{{ endpoint.path }}";
            {% endif %}

            {% if endpoint.query_params %}
            var queryParams = HttpUtility.ParseQueryString(string.Empty);
            {% for param in endpoint.query_params %}
            {% if param.required %}
            queryParams["{{ param.name }}"] = {{ param.name }}?.ToString() ?? "";
            {% else %}
            if ({{ param.name }} != null)
            {
                queryParams["{{ param.name }}"] = {{ param.name }}.ToString();
            }
            {% endif %}
            {% endfor %}

            if (queryParams.Count > 0)
            {
                path += $"?{queryParams}";
            }
            {% endif %}

            {% if endpoint.has_body %}
            var body = new Dictionary<string, object?>();
            {% for param in endpoint.body_params %}
            {% if param.required %}
            body["{{ param.name }}"] = {{ param.name }};
            {% else %}
            if ({{ param.name }} != null)
            {
                body["{{ param.name }}"] = {{ param.name }};
            }
            {% endif %}
            {% endfor %}

            return await MakeRequestAsync(HttpMethod.{{ endpoint.method.title() }}, path, body, cancellationToken);
            {% else %}
            return await MakeRequestAsync(HttpMethod.{{ endpoint.method.title() }}, path, cancellationToken: cancellationToken);
            {% endif %}
        }

{% endfor %}

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    /// <summary>
    /// Factory class for creating {{ class_name }} instances
    /// </summary>
    public static class {{ class_name }}Factory
    {
        /// <summary>
        /// Create a new {{ class_name }} instance
        /// </summary>
        public static {{ class_name }} Create(
            {% if auth_type == 'api_key' %}
            string apiKey,
            {% elif auth_type == 'bearer_token' %}
            string token,
            {% endif %}
            string? baseUrl = null,
            {{ class_name }}Config? config = null)
        {
            return new {{ class_name }}(
                {% if auth_type == 'api_key' %}
                apiKey,
                {% elif auth_type == 'bearer_token' %}
                token,
                {% endif %}
                baseUrl ?? "{{ base_url }}",
                config);
        }
    }
}
"""

    def get_php_client_template(self) -> str:
        """Complete PHP client template"""
        return """<?php

namespace {{ package_name|replace('-', '\\') |title }};

use Exception;
use GuzzleHttp\\Client;
use GuzzleHttp\\Exception\\GuzzleException;
use GuzzleHttp\\Exception\\RequestException;
use Psr\\Http\\Message\\ResponseInterface;

/**
 * {{ package_name }} - {{ description }}
 * Generated PHP API client for {{ base_url }}
 */

class {{ class_name }}Exception extends Exception
{
    private int $statusCode;
    private ?string $responseBody;

    public function __construct(string $message, int $statusCode = 0, ?string $responseBody = null, Exception $previous = null)
    {
        parent::__construct($message, $statusCode, $previous);
        $this->statusCode = $statusCode;
        $this->responseBody = $responseBody;
    }

    public function getStatusCode(): int
    {
        return $this->statusCode;
    }

    public function getResponseBody(): ?string
    {
        return $this->responseBody;
    }
}

class {{ class_name }}Config
{
    public float $timeout = 30.0;
    {% if include_retry_logic %}
    public int $maxRetries = 3;
    public float $retryDelay = 1.0;
    {% endif %}
    {% if include_rate_limiting %}
    public int $rateLimit = 100;
    {% endif %}

    public function __construct(array $options = [])
    {
        foreach ($options as $key => $value) {
            if (property_exists($this, $key)) {
                $this->{$key} = $value;
            }
        }
    }
}

class {{ class_name }}
{
    private Client $httpClient;
    private string $baseUrl;
    {% if auth_type == 'api_key' %}
    private string $apiKey;
    {% elif auth_type == 'bearer_token' %}
    private string $token;
    {% endif %}
    private {{ class_name }}Config $config;

    {% if include_rate_limiting %}
    private int $rateLimitCalls = 0;
    private float $rateLimitReset;
    {% endif %}

    /**
     * Initialize the API client
     *
     * @param string ${% if auth_type == 'api_key' %}apiKey Your API key{% elif auth_type == 'bearer_token' %}token Your bearer token{% endif %}
     * @param string $baseUrl Base URL for the API
     * @param {{ class_name }}Config|null $config Client configuration
     * @param Client|null $httpClient Custom HTTP client
     */
    public function __construct(
        {% if auth_type == 'api_key' %}
        string $apiKey,
        {% elif auth_type == 'bearer_token' %}
        string $token,
        {% endif %}
        string $baseUrl = '{{ base_url }}',
        ?{{ class_name }}Config $config = null,
        ?Client $httpClient = null
    ) {
        $this->baseUrl = rtrim($baseUrl, '/');
        {% if auth_type == 'api_key' %}
        $this->apiKey = $apiKey;
        {% elif auth_type == 'bearer_token' %}
        $this->token = $token;
        {% endif %}
        $this->config = $config ?? new {{ class_name }}Config();

        $this->httpClient = $httpClient ?? new Client([
            'timeout' => $this->config->timeout,
            'headers' => $this->getDefaultHeaders(),
        ]);

        {% if include_rate_limiting %}
        $this->rateLimitReset = microtime(true);
        {% endif %}
    }

    private function getDefaultHeaders(): array
    {
        $headers = [
            'Content-Type' => 'application/json',
            'User-Agent' => '{{ package_name }}/{{ version }}',
        ];

        {% if auth_type == 'api_key' %}
        $headers['X-API-Key'] = $this->apiKey;
        {% elif auth_type == 'bearer_token' %}
        $headers['Authorization'] = 'Bearer ' . $this->token;
        {% endif %}

        return $headers;
    }

    {% if include_rate_limiting %}
    private function checkRateLimit(): void
    {
        if ($this->rateLimitCalls >= $this->config->rateLimit) {
            $elapsed = microtime(true) - $this->rateLimitReset;
            if ($elapsed < 60) {
                $waitTime = 60 - $elapsed;
                usleep((int)($waitTime * 1000000));
                $this->rateLimitCalls = 0;
                $this->rateLimitReset = microtime(true);
            }
        }
    }
    {% endif %}

    {% if include_retry_logic %}
    private function makeRequestWithRetry(callable $request): array
    {
        $lastException = null;

        for ($attempt = 0; $attempt <= $this->config->maxRetries; $attempt++) {
            try {
                return $request();
            } catch ({{ class_name }}Exception $e) {
                // Don't retry client errors (4xx)
                if ($e->getStatusCode() >= 400 && $e->getStatusCode() < 500) {
                    throw $e;
                }
                $lastException = $e;

                if ($attempt < $this->config->maxRetries) {
                    usleep((int)($this->config->retryDelay * 1000000 * ($attempt + 1)));
                }
            } catch (Exception $e) {
                $lastException = $e;

                if ($attempt < $this->config->maxRetries) {
                    usleep((int)($this->config->retryDelay * 1000000 * ($attempt + 1)));
                }
            }
        }

        throw $lastException ?? new {{ class_name }}Exception('Max retries exceeded');
    }
    {% endif %}

    private function makeRequest(string $method, string $endpoint, ?array $body = null): array
    {
        {% if include_rate_limiting %}
        $this->checkRateLimit();
        {% endif %}

        $url = $this->baseUrl . $endpoint;

        {% if include_retry_logic %}
        return $this->makeRequestWithRetry(function () use ($method, $url, $body) {
        {% endif %}
            $options = [
                'headers' => $this->getDefaultHeaders(),
            ];

            if ($body !== null) {
                $options['json'] = $body;
            }

            try {
                $response = $this->httpClient->request($method, $url, $options);

                {% if include_rate_limiting %}
                $this->rateLimitCalls++;
                {% endif %}

                return $this->handleResponse($response);
            } catch (RequestException $e) {
                $response = $e->getResponse();
                $statusCode = $response ? $response->getStatusCode() : 0;
                $responseBody = $response ? $response->getBody()->getContents() : null;

                throw new {{ class_name }}Exception(
                    "API request failed: {$statusCode} - " . ($responseBody ?? $e->getMessage()),
                    $statusCode,
                    $responseBody,
                    $e
                );
            } catch (GuzzleException $e) {
                throw new {{ class_name }}Exception(
                    "HTTP request failed: " . $e->getMessage(),
                    0,
                    null,
                    $e
                );
            }
        {% if include_retry_logic %}
        });
        {% endif %}
    }

    private function handleResponse(ResponseInterface $response): array
    {
        $statusCode = $response->getStatusCode();
        $body = $response->getBody()->getContents();

        if ($statusCode >= 400) {
            throw new {{ class_name }}Exception(
                "API request failed: {$statusCode} - {$body}",
                $statusCode,
                $body
            );
        }

        $decoded = json_decode($body, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return ['data' => $body];
        }

        return $decoded;
    }

{% for endpoint in endpoints %}
    /**
     * {{ endpoint.description or endpoint.summary or 'API endpoint' }}
     *
     {% for param in endpoint.parameters %}
     * @param {{ param.type }} ${{ param.name }} {{ param.description or param.name }}
     {% endfor %}
     * @return array
     * @throws {{ class_name }}Exception
     */
    public function {{ endpoint.method_name }}(
        {% for param in endpoint.parameters %}
        {% if not param.required %}?{% endif %}{{ param.type }} ${{ param.name }}{% if not param.required %} = null{% endif %}{% if not loop.last %},{% endif %}
        {% endfor %}
    ): array {
        {% if endpoint.path_params %}
        $path = '{{ endpoint.path }}';
        {% for param in endpoint.path_params %}
        $path = str_replace('{{{ param.name }}}', (string)${{ param.name }}, $path);
        {% endfor %}
        {% else %}
        $path = '{{ endpoint.path }}';
        {% endif %}

        {% if endpoint.query_params %}
        $queryParams = [];
        {% for param in endpoint.query_params %}
        {% if param.required %}
        $queryParams['{{ param.name }}'] = (string)${{ param.name }};
        {% else %}
        if (${{ param.name }} !== null) {
            $queryParams['{{ param.name }}'] = (string)${{ param.name }};
        }
        {% endif %}
        {% endfor %}

        if (!empty($queryParams)) {
            $path .= '?' . http_build_query($queryParams);
        }
        {% endif %}

        {% if endpoint.has_body %}
        $body = [];
        {% for param in endpoint.body_params %}
        {% if param.required %}
        $body['{{ param.name }}'] = ${{ param.name }};
        {% else %}
        if (${{ param.name }} !== null) {
            $body['{{ param.name }}'] = ${{ param.name }};
        }
        {% endif %}
        {% endfor %}

        return $this->makeRequest('{{ endpoint.method.upper() }}', $path, $body);
        {% else %}
        return $this->makeRequest('{{ endpoint.method.upper() }}', $path);
        {% endif %}
    }

{% endfor %}
}

/**
 * Create a new {{ class_name }} instance
 */
function create{{ class_name }}(
    {% if auth_type == 'api_key' %}
    string $apiKey,
    {% elif auth_type == 'bearer_token' %}
    string $token,
    {% endif %}
    string $baseUrl = '{{ base_url }}',
    ?{{ class_name }}Config $config = null
): {{ class_name }} {
    return new {{ class_name }}(
        {% if auth_type == 'api_key' %}
        $apiKey,
        {% elif auth_type == 'bearer_token' %}
        $token,
        {% endif %}
        $baseUrl,
        $config
    );
}
"""

    def get_ruby_client_template(self) -> str:
        """Complete Ruby client template"""
        return """# {{ package_name }} - {{ description }}
# Generated Ruby API client for {{ base_url }}

require 'net/http'
require 'uri'
require 'json'
require 'time'

module {{ package_name|replace('-', '_')|title }}
  # Custom exception for API errors
  class {{ class_name }}Error < StandardError
    attr_reader :status_code, :response_body

    def initialize(message, status_code = nil, response_body = nil)
      super(message)
      @status_code = status_code
      @response_body = response_body
    end
  end

  # Configuration class for the API client
  class {{ class_name }}Config
    attr_accessor :timeout{% if include_retry_logic %}, :max_retries, :retry_delay{% endif %}{% if include_rate_limiting %}, :rate_limit{% endif %}

    def initialize(options = {})
      @timeout = options[:timeout] || 30
      {% if include_retry_logic %}
      @max_retries = options[:max_retries] || 3
      @retry_delay = options[:retry_delay] || 1
      {% endif %}
      {% if include_rate_limiting %}
      @rate_limit = options[:rate_limit] || 100
      {% endif %}
    end
  end

  # Main API client class
  class {{ class_name }}
    {% if auth_type == 'api_key' %}
    attr_reader :api_key, :base_url, :config
    {% elif auth_type == 'bearer_token' %}
    attr_reader :token, :base_url, :config
    {% endif %}

    def initialize({% if auth_type == 'api_key' %}api_key:,{% elif auth_type == 'bearer_token' %}token:,{% endif %} base_url: '{{ base_url }}', config: nil)
      {% if auth_type == 'api_key' %}
      @api_key = api_key
      {% elif auth_type == 'bearer_token' %}
      @token = token
      {% endif %}
      @base_url = base_url.chomp('/')
      @config = config || {{ class_name }}Config.new

      {% if include_rate_limiting %}
      @rate_limit_calls = 0
      @rate_limit_reset = Time.now
      {% endif %}
    end

    private

    def default_headers
      headers = {
        'Content-Type' => 'application/json',
        'User-Agent' => '{{ package_name }}/{{ version }}'
      }

      {% if auth_type == 'api_key' %}
      headers['X-API-Key'] = @api_key
      {% elif auth_type == 'bearer_token' %}
      headers['Authorization'] = "Bearer #{@token}"
      {% endif %}

      headers
    end

    {% if include_rate_limiting %}
    def check_rate_limit
      return unless @rate_limit_calls >= @config.rate_limit

      elapsed = Time.now - @rate_limit_reset
      return unless elapsed < 60

      wait_time = 60 - elapsed
      sleep(wait_time)
      @rate_limit_calls = 0
      @rate_limit_reset = Time.now
    end
    {% endif %}

    {% if include_retry_logic %}
    def make_request_with_retry(method, uri, body = nil)
      last_exception = nil

      (0..@config.max_retries).each do |attempt|
        begin
          return make_request_internal(method, uri, body)
        rescue {{ class_name }}Error => e
          # Don't retry client errors (4xx)
          raise e if e.status_code && e.status_code >= 400 && e.status_code < 500

          last_exception = e
          sleep(@config.retry_delay * (attempt + 1)) if attempt < @config.max_retries
        rescue StandardError => e
          last_exception = e
          sleep(@config.retry_delay * (attempt + 1)) if attempt < @config.max_retries
        end
      end

      raise last_exception || {{ class_name }}Error.new('Max retries exceeded')
    end
    {% endif %}

    def make_request_internal(method, uri, body = nil)
      {% if include_rate_limiting %}
      check_rate_limit
      {% endif %}

      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == 'https'
      http.read_timeout = @config.timeout
      http.open_timeout = @config.timeout

      request = case method.upcase
                when 'GET'
                  Net::HTTP::Get.new(uri)
                when 'POST'
                  Net::HTTP::Post.new(uri)
                when 'PUT'
                  Net::HTTP::Put.new(uri)
                when 'DELETE'
                  Net::HTTP::Delete.new(uri)
                else
                  raise {{ class_name }}Error.new("Unsupported HTTP method: #{method}")
                end

      default_headers.each { |key, value| request[key] = value }

      if body && !body.empty?
        request.body = body.is_a?(String) ? body : JSON.generate(body)
      end

      response = http.request(request)

      {% if include_rate_limiting %}
      @rate_limit_calls += 1
      {% endif %}

      handle_response(response)
    end

    def make_request(method, endpoint, body = nil)
      url = "#{@base_url}#{endpoint}"
      uri = URI(url)

      {% if include_retry_logic %}
      make_request_with_retry(method, uri, body)
      {% else %}
      make_request_internal(method, uri, body)
      {% endif %}
    end

    def handle_response(response)
      case response.code.to_i
      when 200..299
        begin
          JSON.parse(response.body)
        rescue JSON::ParserError
          { 'data' => response.body }
        end
      else
        raise {{ class_name }}Error.new(
          "API request failed: #{response.code} - #{response.body}",
          response.code.to_i,
          response.body
        )
      end
    end

    public

{% for endpoint in endpoints %}
    # {{ endpoint.description or endpoint.summary or 'API endpoint' }}
    #
    # @param [Hash] params Parameters for the request
    {% for param in endpoint.parameters %}
    # @option params [{{ param.type }}] :{{ param.name }}{% if not param.required %} (optional){% endif %} {{ param.description or param.name }}
    {% endfor %}
    # @return [Hash] API response
    # @raise [{{ class_name }}Error] When the API request fails
    def {{ endpoint.method_name }}(params = {})
      {% if endpoint.path_params %}
      path = '{{ endpoint.path }}'
      {% for param in endpoint.path_params %}
      path = path.gsub('{{{ param.name }}}', params[:{{ param.name }}].to_s)
      {% endfor %}
      {% else %}
      path = '{{ endpoint.path }}'
      {% endif %}

      {% if endpoint.query_params %}
      query_params = []
      {% for param in endpoint.query_params %}
      {% if param.required %}
      query_params << "{{ param.name }}=#{CGI.escape(params[:{{ param.name }}].to_s)}"
      {% else %}
      query_params << "{{ param.name }}=#{CGI.escape(params[:{{ param.name }}].to_s)}" if params[:{{ param.name }}]
      {% endif %}
      {% endfor %}

      path += "?#{query_params.join('&')}" unless query_params.empty?
      {% endif %}

      {% if endpoint.has_body %}
      body = {}
      {% for param in endpoint.body_params %}
      {% if param.required %}
      body['{{ param.name }}'] = params[:{{ param.name }}]
      {% else %}
      body['{{ param.name }}'] = params[:{{ param.name }}] if params[:{{ param.name }}]
      {% endif %}
      {% endfor %}

      make_request('{{ endpoint.method.upper() }}', path, body)
      {% else %}
      make_request('{{ endpoint.method.upper() }}', path)
      {% endif %}
    end

{% endfor %}
  end

  # Factory method to create a new client instance
  def self.create_client({% if auth_type == 'api_key' %}api_key:,{% elif auth_type == 'bearer_token' %}token:,{% endif %} base_url: '{{ base_url }}', config: nil)
    {{ class_name }}.new(
      {% if auth_type == 'api_key' %}
      api_key: api_key,
      {% elif auth_type == 'bearer_token' %}
      token: token,
      {% endif %}
      base_url: base_url,
      config: config
    )
  end
end
"""
