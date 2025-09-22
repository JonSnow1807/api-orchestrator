"""
Kubernetes Deployment Manifests Generator
Enterprise-grade Kubernetes configurations for API Orchestrator
"""

import yaml
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DeploymentConfig:
    """Deployment configuration settings"""
    app_name: str = "api-orchestrator"
    namespace: str = "api-orchestrator"
    image: str = "api-orchestrator:latest"
    replicas: int = 3
    environment: str = "production"

    # Resource specifications
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "1Gi"
    memory_limit: str = "4Gi"

    # Auto-scaling settings
    min_replicas: int = 2
    max_replicas: int = 20
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80

    # Database settings
    database_url: str = "postgresql://user:pass@postgres:5432/api_orchestrator"
    redis_url: str = "redis://redis:6379/0"

    # Security settings
    enable_pod_security_policy: bool = True
    enable_network_policy: bool = True

    # Monitoring settings
    enable_prometheus_monitoring: bool = True
    enable_jaeger_tracing: bool = True

class KubernetesManifestGenerator:
    """Generate Kubernetes manifests for API Orchestrator deployment"""

    def __init__(self, config: DeploymentConfig):
        self.config = config

    def generate_all_manifests(self) -> Dict[str, Dict[str, Any]]:
        """Generate all Kubernetes manifests"""
        manifests = {
            "namespace": self.generate_namespace(),
            "configmap": self.generate_configmap(),
            "secret": self.generate_secret(),
            "deployment": self.generate_deployment(),
            "service": self.generate_service(),
            "ingress": self.generate_ingress(),
            "hpa": self.generate_hpa(),
            "pdb": self.generate_pod_disruption_budget(),
            "network_policy": self.generate_network_policy(),
            "service_monitor": self.generate_service_monitor(),
            "redis_deployment": self.generate_redis_deployment(),
            "redis_service": self.generate_redis_service(),
            "postgres_deployment": self.generate_postgres_deployment(),
            "postgres_service": self.generate_postgres_service(),
            "postgres_pvc": self.generate_postgres_pvc()
        }

        if self.config.enable_pod_security_policy:
            manifests["pod_security_policy"] = self.generate_pod_security_policy()

        return manifests

    def generate_namespace(self) -> Dict[str, Any]:
        """Generate namespace manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": self.config.namespace,
                "labels": {
                    "name": self.config.namespace,
                    "app": self.config.app_name,
                    "environment": self.config.environment
                }
            }
        }

    def generate_configmap(self) -> Dict[str, Any]:
        """Generate ConfigMap manifest"""
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{self.config.app_name}-config",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "config"
                }
            },
            "data": {
                "ENVIRONMENT": self.config.environment,
                "LOG_LEVEL": "INFO",
                "REDIS_URL": self.config.redis_url,
                "ENABLE_PROMETHEUS_METRICS": "true",
                "ENABLE_JAEGER_TRACING": str(self.config.enable_jaeger_tracing).lower(),
                "API_VERSION": "v1",
                "CORS_ORIGINS": "*",
                "MAX_WORKERS": "4",
                "WORKER_CLASS": "uvicorn.workers.UvicornWorker"
            }
        }

    def generate_secret(self) -> Dict[str, Any]:
        """Generate Secret manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{self.config.app_name}-secrets",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "secrets"
                }
            },
            "type": "Opaque",
            "data": {
                # These should be base64 encoded in real deployment
                "DATABASE_URL": "cG9zdGdyZXNxbDovL3VzZXI6cGFzc0Bwb3N0Z3Jlczo1NDMyL2FwaV9vcmNoZXN0cmF0b3I=",
                "SECRET_KEY": "Y2hhbmdlLW1lLWluLXByb2R1Y3Rpb24=",
                "JWT_SECRET_KEY": "Y2hhbmdlLW1lLWluLXByb2R1Y3Rpb24=",
                "ENCRYPTION_KEY": "Y2hhbmdlLW1lLWluLXByb2R1Y3Rpb24="
            }
        }

    def generate_deployment(self) -> Dict[str, Any]:
        """Generate Deployment manifest"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.config.app_name,
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "version": "v1",
                    "component": "api"
                }
            },
            "spec": {
                "replicas": self.config.replicas,
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxSurge": 1,
                        "maxUnavailable": 0
                    }
                },
                "selector": {
                    "matchLabels": {
                        "app": self.config.app_name,
                        "component": "api"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": self.config.app_name,
                            "version": "v1",
                            "component": "api"
                        },
                        "annotations": {
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "8000",
                            "prometheus.io/path": "/metrics"
                        }
                    },
                    "spec": {
                        "serviceAccountName": f"{self.config.app_name}-service-account",
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "fsGroup": 1000
                        },
                        "containers": [
                            {
                                "name": self.config.app_name,
                                "image": self.config.image,
                                "imagePullPolicy": "IfNotPresent",
                                "ports": [
                                    {
                                        "name": "http",
                                        "containerPort": 8000,
                                        "protocol": "TCP"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "PORT",
                                        "value": "8000"
                                    }
                                ],
                                "envFrom": [
                                    {
                                        "configMapRef": {
                                            "name": f"{self.config.app_name}-config"
                                        }
                                    },
                                    {
                                        "secretRef": {
                                            "name": f"{self.config.app_name}-secrets"
                                        }
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": self.config.cpu_request,
                                        "memory": self.config.memory_request
                                    },
                                    "limits": {
                                        "cpu": self.config.cpu_limit,
                                        "memory": self.config.memory_limit
                                    }
                                },
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": "http"
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10,
                                    "timeoutSeconds": 5,
                                    "failureThreshold": 3
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": "http"
                                    },
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5,
                                    "timeoutSeconds": 3,
                                    "failureThreshold": 3
                                },
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "readOnlyRootFilesystem": True,
                                    "capabilities": {
                                        "drop": ["ALL"]
                                    }
                                },
                                "volumeMounts": [
                                    {
                                        "name": "tmp",
                                        "mountPath": "/tmp"
                                    }
                                ]
                            }
                        ],
                        "volumes": [
                            {
                                "name": "tmp",
                                "emptyDir": {}
                            }
                        ],
                        "terminationGracePeriodSeconds": 30,
                        "dnsPolicy": "ClusterFirst",
                        "restartPolicy": "Always"
                    }
                }
            }
        }

    def generate_service(self) -> Dict[str, Any]:
        """Generate Service manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{self.config.app_name}-service",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "api"
                }
            },
            "spec": {
                "type": "ClusterIP",
                "ports": [
                    {
                        "name": "http",
                        "port": 80,
                        "targetPort": "http",
                        "protocol": "TCP"
                    }
                ],
                "selector": {
                    "app": self.config.app_name,
                    "component": "api"
                }
            }
        }

    def generate_ingress(self) -> Dict[str, Any]:
        """Generate Ingress manifest"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{self.config.app_name}-ingress",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "ingress"
                },
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "nginx.ingress.kubernetes.io/use-regex": "true",
                    "nginx.ingress.kubernetes.io/rewrite-target": "/$1",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                    "nginx.ingress.kubernetes.io/rate-limit": "100",
                    "nginx.ingress.kubernetes.io/rate-limit-window": "1m"
                }
            },
            "spec": {
                "tls": [
                    {
                        "hosts": ["api.yourdomain.com"],
                        "secretName": f"{self.config.app_name}-tls"
                    }
                ],
                "rules": [
                    {
                        "host": "api.yourdomain.com",
                        "http": {
                            "paths": [
                                {
                                    "path": "/(.*)",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": f"{self.config.app_name}-service",
                                            "port": {
                                                "number": 80
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    def generate_hpa(self) -> Dict[str, Any]:
        """Generate HorizontalPodAutoscaler manifest"""
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{self.config.app_name}-hpa",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "autoscaler"
                }
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.config.app_name
                },
                "minReplicas": self.config.min_replicas,
                "maxReplicas": self.config.max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": self.config.target_cpu_utilization
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": self.config.target_memory_utilization
                            }
                        }
                    }
                ],
                "behavior": {
                    "scaleUp": {
                        "stabilizationWindowSeconds": 300,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 100,
                                "periodSeconds": 15
                            },
                            {
                                "type": "Pods",
                                "value": 2,
                                "periodSeconds": 60
                            }
                        ],
                        "selectPolicy": "Max"
                    },
                    "scaleDown": {
                        "stabilizationWindowSeconds": 300,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 10,
                                "periodSeconds": 60
                            }
                        ]
                    }
                }
            }
        }

    def generate_pod_disruption_budget(self) -> Dict[str, Any]:
        """Generate PodDisruptionBudget manifest"""
        return {
            "apiVersion": "policy/v1",
            "kind": "PodDisruptionBudget",
            "metadata": {
                "name": f"{self.config.app_name}-pdb",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "disruption-budget"
                }
            },
            "spec": {
                "minAvailable": 1,
                "selector": {
                    "matchLabels": {
                        "app": self.config.app_name,
                        "component": "api"
                    }
                }
            }
        }

    def generate_network_policy(self) -> Dict[str, Any]:
        """Generate NetworkPolicy manifest"""
        if not self.config.enable_network_policy:
            return {}

        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": f"{self.config.app_name}-network-policy",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "network-policy"
                }
            },
            "spec": {
                "podSelector": {
                    "matchLabels": {
                        "app": self.config.app_name
                    }
                },
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {
                                        "name": "nginx-ingress"
                                    }
                                }
                            }
                        ],
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": 8000
                            }
                        ]
                    }
                ],
                "egress": [
                    {
                        "to": [
                            {
                                "podSelector": {
                                    "matchLabels": {
                                        "app": "postgres"
                                    }
                                }
                            }
                        ],
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": 5432
                            }
                        ]
                    },
                    {
                        "to": [
                            {
                                "podSelector": {
                                    "matchLabels": {
                                        "app": "redis"
                                    }
                                }
                            }
                        ],
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": 6379
                            }
                        ]
                    },
                    {
                        "to": [],
                        "ports": [
                            {
                                "protocol": "TCP",
                                "port": 53
                            },
                            {
                                "protocol": "UDP",
                                "port": 53
                            }
                        ]
                    }
                ]
            }
        }

    def generate_service_monitor(self) -> Dict[str, Any]:
        """Generate ServiceMonitor for Prometheus"""
        if not self.config.enable_prometheus_monitoring:
            return {}

        return {
            "apiVersion": "monitoring.coreos.com/v1",
            "kind": "ServiceMonitor",
            "metadata": {
                "name": f"{self.config.app_name}-metrics",
                "namespace": self.config.namespace,
                "labels": {
                    "app": self.config.app_name,
                    "component": "monitoring"
                }
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": self.config.app_name,
                        "component": "api"
                    }
                },
                "endpoints": [
                    {
                        "port": "http",
                        "path": "/metrics",
                        "interval": "30s",
                        "scrapeTimeout": "10s"
                    }
                ]
            }
        }

    def generate_redis_deployment(self) -> Dict[str, Any]:
        """Generate Redis deployment manifest"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "redis",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "redis",
                    "component": "cache"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "redis"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "redis"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "redis",
                                "image": "redis:7-alpine",
                                "ports": [
                                    {
                                        "containerPort": 6379
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    },
                                    "limits": {
                                        "cpu": "500m",
                                        "memory": "512Mi"
                                    }
                                },
                                "livenessProbe": {
                                    "tcpSocket": {
                                        "port": 6379
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                }
                            }
                        ]
                    }
                }
            }
        }

    def generate_redis_service(self) -> Dict[str, Any]:
        """Generate Redis service manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "redis",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "redis"
                }
            },
            "spec": {
                "ports": [
                    {
                        "port": 6379,
                        "targetPort": 6379
                    }
                ],
                "selector": {
                    "app": "redis"
                }
            }
        }

    def generate_postgres_deployment(self) -> Dict[str, Any]:
        """Generate PostgreSQL deployment manifest"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "postgres",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "postgres",
                    "component": "database"
                }
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "postgres"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "postgres"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "postgres",
                                "image": "postgres:15-alpine",
                                "env": [
                                    {
                                        "name": "POSTGRES_DB",
                                        "value": "api_orchestrator"
                                    },
                                    {
                                        "name": "POSTGRES_USER",
                                        "value": "user"
                                    },
                                    {
                                        "name": "POSTGRES_PASSWORD",
                                        "value": "pass"
                                    }
                                ],
                                "ports": [
                                    {
                                        "containerPort": 5432
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "250m",
                                        "memory": "512Mi"
                                    },
                                    "limits": {
                                        "cpu": "1000m",
                                        "memory": "2Gi"
                                    }
                                },
                                "volumeMounts": [
                                    {
                                        "name": "postgres-storage",
                                        "mountPath": "/var/lib/postgresql/data"
                                    }
                                ],
                                "livenessProbe": {
                                    "exec": {
                                        "command": [
                                            "pg_isready",
                                            "-U",
                                            "user",
                                            "-d",
                                            "api_orchestrator"
                                        ]
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                }
                            }
                        ],
                        "volumes": [
                            {
                                "name": "postgres-storage",
                                "persistentVolumeClaim": {
                                    "claimName": "postgres-pvc"
                                }
                            }
                        ]
                    }
                }
            }
        }

    def generate_postgres_service(self) -> Dict[str, Any]:
        """Generate PostgreSQL service manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "postgres",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "postgres"
                }
            },
            "spec": {
                "ports": [
                    {
                        "port": 5432,
                        "targetPort": 5432
                    }
                ],
                "selector": {
                    "app": "postgres"
                }
            }
        }

    def generate_postgres_pvc(self) -> Dict[str, Any]:
        """Generate PostgreSQL PersistentVolumeClaim manifest"""
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": "postgres-pvc",
                "namespace": self.config.namespace,
                "labels": {
                    "app": "postgres",
                    "component": "storage"
                }
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": "10Gi"
                    }
                },
                "storageClassName": "fast-ssd"
            }
        }

    def generate_pod_security_policy(self) -> Dict[str, Any]:
        """Generate PodSecurityPolicy manifest"""
        return {
            "apiVersion": "policy/v1beta1",
            "kind": "PodSecurityPolicy",
            "metadata": {
                "name": f"{self.config.app_name}-psp",
                "labels": {
                    "app": self.config.app_name,
                    "component": "security"
                }
            },
            "spec": {
                "privileged": False,
                "allowPrivilegeEscalation": False,
                "requiredDropCapabilities": ["ALL"],
                "volumes": [
                    "configMap",
                    "emptyDir",
                    "projected",
                    "secret",
                    "downwardAPI",
                    "persistentVolumeClaim"
                ],
                "runAsUser": {
                    "rule": "MustRunAsNonRoot"
                },
                "seLinux": {
                    "rule": "RunAsAny"
                },
                "fsGroup": {
                    "rule": "RunAsAny"
                }
            }
        }

    def save_manifests_to_files(self, output_dir: str = "k8s-manifests") -> None:
        """Save all manifests to YAML files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        manifests = self.generate_all_manifests()

        for manifest_name, manifest_content in manifests.items():
            if manifest_content:  # Skip empty manifests
                file_path = output_path / f"{manifest_name}.yaml"
                with open(file_path, "w") as f:
                    yaml.dump(manifest_content, f, default_flow_style=False)
                print(f"Generated: {file_path}")

def main():
    """Generate Kubernetes manifests for different environments"""

    # Production configuration
    prod_config = DeploymentConfig(
        environment="production",
        replicas=5,
        min_replicas=3,
        max_replicas=50,
        cpu_request="1000m",
        cpu_limit="4000m",
        memory_request="2Gi",
        memory_limit="8Gi",
        enable_pod_security_policy=True,
        enable_network_policy=True,
        enable_prometheus_monitoring=True,
        enable_jaeger_tracing=True
    )

    # Staging configuration
    staging_config = DeploymentConfig(
        environment="staging",
        namespace="api-orchestrator-staging",
        replicas=2,
        min_replicas=1,
        max_replicas=10,
        cpu_request="500m",
        cpu_limit="2000m",
        memory_request="1Gi",
        memory_limit="4Gi"
    )

    # Development configuration
    dev_config = DeploymentConfig(
        environment="development",
        namespace="api-orchestrator-dev",
        replicas=1,
        min_replicas=1,
        max_replicas=3,
        cpu_request="250m",
        cpu_limit="1000m",
        memory_request="512Mi",
        memory_limit="2Gi",
        enable_pod_security_policy=False,
        enable_network_policy=False
    )

    # Generate manifests for all environments
    environments = [
        ("production", prod_config),
        ("staging", staging_config),
        ("development", dev_config)
    ]

    for env_name, config in environments:
        print(f"\nGenerating Kubernetes manifests for {env_name} environment...")
        generator = KubernetesManifestGenerator(config)
        generator.save_manifests_to_files(f"k8s-manifests-{env_name}")
        print(f"✅ {env_name.title()} manifests generated successfully!")

if __name__ == "__main__":
    main()