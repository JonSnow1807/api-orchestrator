#!/usr/bin/env groovy

/**
 * API Orchestrator - Jenkins Pipeline Template
 * Enterprise-grade API testing pipeline
 */

pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Target environment for testing'
        )
        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security vulnerability scans'
        )
        booleanParam(
            name: 'RUN_PERFORMANCE_TEST',
            defaultValue: false,
            description: 'Run performance load tests'
        )
    }

    environment {
        API_ORCHESTRATOR_URL = credentials('api-orchestrator-url')
        API_ORCHESTRATOR_KEY = credentials('api-orchestrator-key')
        SLACK_WEBHOOK = credentials('slack-webhook-url')
        PATH = "${PATH}:${HOME}/.local/bin"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        retry(2)
        skipStagesAfterUnstable()
    }

    stages {
        stage('Setup') {
            steps {
                script {
                    echo "🔧 Setting up API Orchestrator CLI..."
                    sh '''
                        python3 -m pip install --upgrade pip
                        pip3 install api-orchestrator-cli[ci]
                        api-orchestrator --version
                    '''
                }
            }
        }

        stage('Validate Collections') {
            steps {
                script {
                    echo "🔍 Validating API collections..."
                    sh '''
                        find . -name "*.postman_collection.json" -o -name "*.aorch.json" | \
                        xargs -I {} api-orchestrator validate {}

                        api-orchestrator lint \
                            --collection tests/api-collection.json \
                            --output validation-results.xml
                    '''
                }
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'validation-results.xml'
                }
            }
        }

        stage('API Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        script {
                            echo "🧪 Running API unit tests..."
                            sh """
                                api-orchestrator run \
                                    --collection tests/unit-tests.json \
                                    --environment envs/${params.ENVIRONMENT}.json \
                                    --reporters cli,junit,json \
                                    --output-dir results/unit \
                                    --parallel 3 \
                                    --timeout 15000
                            """
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'results/unit/junit.xml'
                            archiveArtifacts artifacts: 'results/unit/**', allowEmptyArchive: true
                        }
                    }
                }

                stage('Integration Tests') {
                    steps {
                        script {
                            echo "🔗 Running API integration tests..."
                            sh """
                                api-orchestrator run \
                                    --collection tests/integration-tests.json \
                                    --environment envs/${params.ENVIRONMENT}.json \
                                    --reporters cli,junit,json \
                                    --output-dir results/integration \
                                    --timeout 30000 \
                                    --retry 2
                            """
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'results/integration/junit.xml'
                            archiveArtifacts artifacts: 'results/integration/**', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Security Scan') {
            when {
                expression { params.RUN_SECURITY_SCAN }
            }
            steps {
                script {
                    echo "🛡️ Running security vulnerability scan..."
                    sh '''
                        api-orchestrator security-scan \
                            --collection tests/api-collection.json \
                            --output results/security-report.json \
                            --severity medium \
                            --format sarif
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'results/security-report.*', allowEmptyArchive: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'results',
                        reportFiles: 'security-report.html',
                        reportName: 'Security Report'
                    ])
                }
            }
        }

        stage('Performance Tests') {
            when {
                anyOf {
                    expression { params.RUN_PERFORMANCE_TEST }
                    expression { params.ENVIRONMENT == 'staging' }
                }
            }
            steps {
                script {
                    echo "⚡ Running performance load tests..."
                    sh '''
                        api-orchestrator load-test \
                            --collection tests/performance.json \
                            --virtual-users 15 \
                            --duration 90s \
                            --ramp-up 20s \
                            --output results/performance.json \
                            --threshold response_time:2000,success_rate:95
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'results/performance.*', allowEmptyArchive: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'results',
                        reportFiles: 'performance.html',
                        reportName: 'Performance Report'
                    ])
                }
            }
        }

        stage('Contract Tests') {
            when {
                expression { params.ENVIRONMENT != 'development' }
            }
            steps {
                script {
                    echo "📋 Running API contract tests..."
                    sh '''
                        api-orchestrator contract-test \
                            --spec openapi.yaml \
                            --collection tests/contract-tests.json \
                            --output results/contract-results.json
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'results/contract-results.*', allowEmptyArchive: true
                }
            }
        }

        stage('Deploy') {
            when {
                allOf {
                    branch 'main'
                    expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
                }
            }
            steps {
                script {
                    echo "🚀 Deploying API changes..."
                    // Add your deployment commands here
                    sh '''
                        echo "Deploying to ${ENVIRONMENT}..."
                        # kubectl apply -f k8s/ || echo "No k8s deployment"
                        # terraform apply -auto-approve || echo "No terraform deployment"
                    '''
                }
            }
        }

        stage('Smoke Tests') {
            when {
                allOf {
                    branch 'main'
                    expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
                }
            }
            steps {
                script {
                    echo "💨 Running post-deployment smoke tests..."
                    sh '''
                        sleep 30  # Wait for deployment to stabilize

                        api-orchestrator run \
                            --collection tests/smoke-tests.json \
                            --environment envs/production.json \
                            --timeout 10000 \
                            --reporter cli \
                            --fail-fast
                    '''
                }
            }
        }

        stage('Generate Documentation') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "📚 Generating API documentation..."
                    sh '''
                        api-orchestrator docs generate \
                            --spec openapi.yaml \
                            --output docs/ \
                            --format html \
                            --theme modern
                    '''
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'docs',
                        reportFiles: 'index.html',
                        reportName: 'API Documentation'
                    ])
                }
            }
        }
    }

    post {
        always {
            // Clean up
            script {
                sh 'rm -rf results/temp || true'
            }
        }

        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    slackSend(
                        channel: '#deployments',
                        color: 'good',
                        message: """
                            ✅ *API Pipeline Success!*

                            *Environment:* ${params.ENVIRONMENT}
                            *Build:* ${env.BUILD_NUMBER}
                            *Duration:* ${currentBuild.durationString}
                            *Branch:* ${env.BRANCH_NAME}

                            All tests passed and deployment completed successfully!
                        """.stripIndent()
                    )
                }
            }
        }

        failure {
            script {
                slackSend(
                    channel: '#api-alerts',
                    color: 'danger',
                    message: """
                        ❌ *API Pipeline Failed!*

                        *Environment:* ${params.ENVIRONMENT}
                        *Build:* ${env.BUILD_NUMBER}
                        *Branch:* ${env.BRANCH_NAME}
                        *Stage:* ${env.STAGE_NAME}

                        Please check the logs: ${env.BUILD_URL}
                    """.stripIndent()
                )
            }
        }

        unstable {
            script {
                slackSend(
                    channel: '#api-alerts',
                    color: 'warning',
                    message: """
                        ⚠️ *API Pipeline Unstable*

                        *Environment:* ${params.ENVIRONMENT}
                        *Build:* ${env.BUILD_NUMBER}

                        Some tests failed but pipeline continued.
                    """.stripIndent()
                )
            }
        }
    }
}