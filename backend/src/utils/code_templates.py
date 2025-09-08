"""
Basic code generation templates (fallback when AI service is unavailable)
"""

def generate_basic_code(language: str, library: str, api_spec: dict, options: dict) -> str:
    """Generate basic code template"""
    
    base_url = api_spec.get('url', 'https://api.example.com')
    method = api_spec.get('method', 'GET')
    path = api_spec.get('path', '/endpoint')
    
    templates = {
        'javascript': f"""// API Client - {library}
const axios = require('{library}');

const client = axios.create({{
    baseURL: '{base_url}',
    timeout: {options.get('timeout', 30000)},
    headers: {{
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
    }}
}});

// Make request
async function makeRequest() {{
    try {{
        const response = await client.{method.lower()}('{path}');
        console.log(response.data);
        return response.data;
    }} catch (error) {{
        console.error('Error:', error.message);
        throw error;
    }}
}}

makeRequest();
""",
        
        'python': f"""# API Client - {library}
import {library}
import os
from dotenv import load_dotenv

load_dotenv()

# Configure client
base_url = '{base_url}'
headers = {{
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {{os.getenv("API_KEY")}}'
}}

# Make request
def make_request():
    try:
        response = {library}.{method.lower()}(
            f'{{base_url}}{path}',
            headers=headers,
            timeout={options.get('timeout', 30)}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'Error: {{e}}')
        raise

if __name__ == '__main__':
    data = make_request()
    print(data)
""",
        
        'typescript': f"""// API Client - TypeScript
import axios from '{library}';

interface APIResponse {{
    data: any;
    status: number;
}}

class APIClient {{
    private client = axios.create({{
        baseURL: '{base_url}',
        timeout: {options.get('timeout', 30000)},
        headers: {{
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_API_KEY'
        }}
    }});
    
    async makeRequest(): Promise<APIResponse> {{
        try {{
            const response = await this.client.{method.lower()}('{path}');
            return {{
                data: response.data,
                status: response.status
            }};
        }} catch (error) {{
            console.error('Error:', error);
            throw error;
        }}
    }}
}}

export default APIClient;
""",
        
        'java': f"""// API Client - Java
import okhttp3.*;
import java.io.IOException;

public class APIClient {{
    private final OkHttpClient client;
    private final String baseUrl = "{base_url}";
    
    public APIClient() {{
        this.client = new OkHttpClient.Builder()
            .connectTimeout({options.get('timeout', 30)}, TimeUnit.SECONDS)
            .build();
    }}
    
    public String makeRequest() throws IOException {{
        Request request = new Request.Builder()
            .url(baseUrl + "{path}")
            .addHeader("Authorization", "Bearer YOUR_API_KEY")
            .build();
        
        try (Response response = client.newCall(request).execute()) {{
            if (!response.isSuccessful()) {{
                throw new IOException("Unexpected code " + response);
            }}
            return response.body().string();
        }}
    }}
}}
""",
        
        'go': f"""// API Client - Go
package main

import (
    "fmt"
    "io/ioutil"
    "net/http"
    "time"
)

func makeRequest() ([]byte, error) {{
    client := &http.Client{{
        Timeout: {options.get('timeout', 30)} * time.Second,
    }}
    
    req, err := http.NewRequest("{method}", "{base_url}{path}", nil)
    if err != nil {{
        return nil, err
    }}
    
    req.Header.Set("Authorization", "Bearer YOUR_API_KEY")
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := client.Do(req)
    if err != nil {{
        return nil, err
    }}
    defer resp.Body.Close()
    
    return ioutil.ReadAll(resp.Body)
}}

func main() {{
    data, err := makeRequest()
    if err != nil {{
        fmt.Println("Error:", err)
        return
    }}
    fmt.Println(string(data))
}}
""",
        
        'csharp': f"""// API Client - C#
using System;
using System.Net.Http;
using System.Threading.Tasks;

public class APIClient
{{
    private readonly HttpClient client;
    
    public APIClient()
    {{
        client = new HttpClient
        {{
            BaseAddress = new Uri("{base_url}"),
            Timeout = TimeSpan.FromSeconds({options.get('timeout', 30)})
        }};
        client.DefaultRequestHeaders.Add("Authorization", "Bearer YOUR_API_KEY");
    }}
    
    public async Task<string> MakeRequestAsync()
    {{
        var response = await client.{method.title()}Async("{path}");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }}
}}
""",
        
        'ruby': f"""# API Client - Ruby
require 'net/http'
require 'json'
require 'uri'

class APIClient
  def initialize
    @base_url = '{base_url}'
  end
  
  def make_request
    uri = URI.parse(@base_url + '{path}')
    
    request = Net::HTTP::{method.capitalize}.new(uri)
    request['Authorization'] = 'Bearer YOUR_API_KEY'
    request['Content-Type'] = 'application/json'
    
    response = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == 'https') do |http|
      http.request(request)
    end
    
    JSON.parse(response.body)
  end
end

client = APIClient.new
puts client.make_request
""",
        
        'php': f"""<?php
// API Client - PHP

class APIClient {{
    private $baseUrl = '{base_url}';
    
    public function makeRequest() {{
        $ch = curl_init();
        
        curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '{path}');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, {options.get('timeout', 30)});
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer YOUR_API_KEY',
            'Content-Type: application/json'
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {{
            throw new Exception("API error: " . $httpCode);
        }}
        
        return json_decode($response, true);
    }}
}}

$client = new APIClient();
$data = $client->makeRequest();
print_r($data);
""",
        
        'rust': f"""// API Client - Rust
use reqwest;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs({options.get('timeout', 30)}))
        .build()?;
    
    let response = client
        .{method.lower()}("{base_url}{path}")
        .header("Authorization", "Bearer YOUR_API_KEY")
        .send()
        .await?;
    
    let body = response.text().await?;
    println!("{{}}", body);
    
    Ok(())
}}
""",
        
        'kotlin': f"""// API Client - Kotlin
import okhttp3.*
import java.io.IOException

class APIClient {{
    private val client = OkHttpClient.Builder()
        .connectTimeout({options.get('timeout', 30)}, TimeUnit.SECONDS)
        .build()
    
    @Throws(IOException::class)
    fun makeRequest(): String {{
        val request = Request.Builder()
            .url("{base_url}{path}")
            .addHeader("Authorization", "Bearer YOUR_API_KEY")
            .build()
        
        client.newCall(request).execute().use {{ response ->
            if (!response.isSuccessful) {{
                throw IOException("Unexpected code $response")
            }}
            return response.body?.string() ?: ""
        }}
    }}
}}

fun main() {{
    val client = APIClient()
    println(client.makeRequest())
}}
"""
    }
    
    # Return template for requested language or generic
    return templates.get(language, f"""// Generic API Client Template
// Language: {language}
// Library: {library}
// Base URL: {base_url}
// Method: {method}
// Path: {path}

// TODO: Implement API client for {language}
// Configure authentication
// Make {method} request to {base_url}{path}
// Handle response
// Handle errors
""")