pipeline {
    agent any

    parameters {
        choice(name: 'DEPLOYMENT_ACTION', choices: ['DEPLOY', 'ROLLBACK'],
               description: 'Deploy a new version or manually roll back to the last known-good version')
        choice(name: 'ENVIRONMENT', choices: ['UAT', 'PRODUCTION'],
               description: 'Target environment')
        string(name: 'VERSION', defaultValue: '',
               description: 'Version/tag to deploy, e.g. 4.2.1')
        choice(name: 'CONFIRM_PROD', choices: ['NO', 'YES'],
               description: 'Must be YES for a PRODUCTION deployment to proceed')
    }

    environment {
        APP_NAME          = 'retail-app'
        HOST_PORT         = '8081'
        CANDIDATE_PORT    = '8091'
        NETWORK           = 'retail-network'
        HEALTH_PATH       = '/health'
        PREVIOUS_TAG_FILE = '.previous_prod_image'
        // Example of pulling a secret without ever printing it:
        // DB_CREDS = credentials('retail-db-credentials')
    }

    stages {

        stage('Validate Parameters') {
            steps {
                script {
                    if (params.ENVIRONMENT == 'PRODUCTION' && params.CONFIRM_PROD != 'YES') {
                        error("BLOCKED: PRODUCTION deployment requires CONFIRM_PROD = YES.")
                    }
                    if (params.VERSION?.trim() == '') {
                        error("VERSION parameter is required.")
                    }
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                }
                echo "Deploying commit ${env.GIT_COMMIT_SHORT} as version ${params.VERSION} to ${params.ENVIRONMENT}"
            }
        }

        stage('Validate Version/Tag Exists') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                sh '''
                    git fetch --tags
                    git rev-parse "v${VERSION}" >/dev/null 2>&1 && echo "Tag v${VERSION} found" || echo "No matching tag - deploying current branch HEAD"
                '''
            }
        }

        stage('Record Previous Production Image') {
            steps {
                script {
                    def previous = sh(
                        script: "docker ps --filter name=${APP_NAME}-prod --format '{{.Image}}' || true",
                        returnStdout: true
                    ).trim()
                    env.PREVIOUS_IMAGE = previous ?: 'none'
                    writeFile file: env.PREVIOUS_TAG_FILE, text: env.PREVIOUS_IMAGE
                    echo "Previous production image recorded: ${env.PREVIOUS_IMAGE}"
                }
            }
        }

        stage('Build Image') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                sh "docker build -t ${APP_NAME}:${params.VERSION} ."
            }
        }

        stage('Start Candidate') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                sh """
                    docker network create ${NETWORK} || true
                    docker rm -f ${APP_NAME}-candidate || true
                    docker run -d --name ${APP_NAME}-candidate \\
                        --network ${NETWORK} \\
                        -p ${CANDIDATE_PORT}:8081 \\
                        -e APP_VERSION=${params.VERSION} \\
                        -e ENVIRONMENT=${params.ENVIRONMENT} \\
                        ${APP_NAME}:${params.VERSION}
                """
            }
        }

        stage('Application Health Check') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                script {
                    sleep(time: 8, unit: 'SECONDS')
                    def status = sh(
                        script: "curl -s -o /dev/null -w '%{http_code}' http://localhost:${CANDIDATE_PORT}${HEALTH_PATH} || echo 000",
                        returnStdout: true
                    ).trim()
                    env.HEALTH_STATUS = status
                    echo "Candidate health check returned HTTP ${status}"
                }
            }
        }

        stage('Promote or Rollback') {
            when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
            steps {
                script {
                    if (env.HEALTH_STATUS == '200') {
                        echo "Health check PASSED - promoting ${params.VERSION} to production."
                        sh """
                            docker rm -f ${APP_NAME}-candidate || true
                            docker rm -f ${APP_NAME}-prod || true
                            docker run -d --name ${APP_NAME}-prod \\
                                --network ${NETWORK} \\
                                -p ${HOST_PORT}:8081 \\
                                -e APP_VERSION=${params.VERSION} \\
                                -e ENVIRONMENT=${params.ENVIRONMENT} \\
                                ${APP_NAME}:${params.VERSION}
                        """
                        echo "OLD VERSION: ${env.PREVIOUS_IMAGE} | NEW VERSION: ${APP_NAME}:${params.VERSION} | FINAL STATE: DEPLOYED"
                    } else {
                        echo "Health check FAILED (HTTP ${env.HEALTH_STATUS}) - rolling back automatically."
                        sh "docker rm -f ${APP_NAME}-candidate || true"
                        if (env.PREVIOUS_IMAGE != 'none') {
                            sh """
                                docker rm -f ${APP_NAME}-prod || true
                                docker run -d --name ${APP_NAME}-prod \\
                                    --network ${NETWORK} \\
                                    -p ${HOST_PORT}:8081 \\
                                    ${env.PREVIOUS_IMAGE}
                            """
                        }
                        echo "OLD VERSION: ${env.PREVIOUS_IMAGE} | NEW VERSION: ${APP_NAME}:${params.VERSION} (REJECTED) | FINAL STATE: ROLLED BACK"
                        currentBuild.result = 'FAILURE'
                        error("Deployment failed health check - automatic rollback executed. Build marked FAILURE.")
                    }
                }
            }
        }

        stage('Manual Rollback') {
            when { expression { params.DEPLOYMENT_ACTION == 'ROLLBACK' } }
            steps {
                script {
                    def previous = readFile(env.PREVIOUS_TAG_FILE).trim()
                    sh """
                        docker rm -f ${APP_NAME}-prod || true
                        docker run -d --name ${APP_NAME}-prod --network ${NETWORK} -p ${HOST_PORT}:8081 ${previous}
                    """
                    echo "Manually rolled back production to ${previous}"
                }
            }
        }
    }

    post {
        always {
            sh "docker ps --filter name=${APP_NAME} && docker images ${APP_NAME}"
        }
        success {
            echo "Pipeline finished: SUCCESS"
        }
        failure {
            echo "Pipeline finished: FAILURE - see console output above for rollback details."
        }
    }
}
