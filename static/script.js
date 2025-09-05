// Modern HR Analytics Dashboard JavaScript

class HRAnalyticsDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.updateConnectionStatus();
        this.setupNavigation();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.showSection(section);
            });
        });

        // Query submission
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.submitQuery();
                }
            });
        }

        // Employee search
        const employeeSearch = document.getElementById('employeeSearch');
        if (employeeSearch) {
            employeeSearch.addEventListener('input', (e) => {
                this.searchEmployees(e.target.value);
            });
        }

        // Quick action buttons
        document.querySelectorAll('.action-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const text = card.querySelector('span').textContent;
                if (text.includes('Ask AI Question')) {
                    this.showSection('query');
                } else if (text.includes('View Analytics')) {
                    this.showSection('analytics');
                } else if (text.includes('Browse Employees')) {
                    this.showSection('employees');
                }
            });
        });
    }

    setupNavigation() {
        // Update page title and subtitle based on current section
        const titles = {
            dashboard: { title: 'Dashboard Overview', subtitle: 'Comprehensive employee analytics and insights' },
            query: { title: 'AI Query Interface', subtitle: 'Ask questions about your employees in natural language' },
            analytics: { title: 'Advanced Analytics', subtitle: 'Deep insights into your workforce data' },
            employees: { title: 'Employee Directory', subtitle: 'Browse and manage your employee database' },
            reports: { title: 'Reports & Documents', subtitle: 'Generate and download comprehensive HR reports' }
        };

        const updatePageTitle = (section) => {
            const titleElement = document.getElementById('pageTitle');
            const subtitleElement = document.getElementById('pageSubtitle');
            
            if (titleElement && subtitleElement && titles[section]) {
                titleElement.textContent = titles[section].title;
                subtitleElement.textContent = titles[section].subtitle;
            }
        };

        // Update title when section changes
        this.updatePageTitle = updatePageTitle;
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Show selected section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
            
            // Update navigation
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const activeNavItem = document.querySelector(`[data-section="${sectionName}"]`);
            if (activeNavItem) {
                activeNavItem.classList.add('active');
            }

            // Update page title
            if (this.updatePageTitle) {
                this.updatePageTitle(sectionName);
            }

            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }

    async loadDashboardData() {
        try {
            // Load metrics
            await this.loadMetrics();
            
            // Load charts data
            await this.loadChartsData();
            
            // Load recent queries
            await this.loadRecentQueries();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showNotification('Error loading dashboard data', 'error');
        }
    }

    async loadMetrics() {
        try {
            const response = await fetch('/api/employee-count');
            const data = await response.json();
            
            // Update total employees
            const totalEmployeesElement = document.getElementById('totalEmployees');
            if (totalEmployeesElement) {
                totalEmployeesElement.textContent = data.count || 0;
            }

            // Load department count
            const deptResponse = await fetch('/api/analytics/departments');
            const deptData = await deptResponse.json();
            
            const totalDepartmentsElement = document.getElementById('totalDepartments');
            if (totalDepartmentsElement) {
                totalDepartmentsElement.textContent = deptData.total_departments || 0;
            }

            // Load performance data
            const perfResponse = await fetch('/api/analytics/performance');
            const perfData = await perfResponse.json();
            
            const avgPerformanceElement = document.getElementById('avgPerformance');
            if (avgPerformanceElement && perfData.performance_ratings && perfData.performance_ratings.length > 0) {
                const avgRating = perfData.performance_ratings.reduce((sum, item) => sum + item.value, 0) / perfData.performance_ratings.length;
                avgPerformanceElement.textContent = avgRating.toFixed(1);
            }

            // Load attrition data
            const attritionResponse = await fetch('/api/analytics/attrition');
            const attritionData = await attritionResponse.json();
            
            const attritionRiskElement = document.getElementById('attritionRisk');
            if (attritionRiskElement && attritionData.attrition_risks) {
                const highRiskCount = attritionData.attrition_risks.filter(item => item.value >= 7).length;
                attritionRiskElement.textContent = highRiskCount;
            }

        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    async loadChartsData() {
        // Placeholder for chart data loading
        // In a real implementation, you would load actual chart data here
        console.log('Loading charts data...');
    }

    async loadRecentQueries() {
        // Placeholder for recent queries
        // In a real implementation, you would load from localStorage or API
        console.log('Loading recent queries...');
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'employees':
                await this.loadEmployees();
                break;
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'advanced-analytics':
                await this.loadAdvancedAnalytics();
                break;
            case 'reports':
                await this.loadReportsData();
                break;
        }
    }

    async loadEmployees() {
        try {
            const response = await fetch('/api/employees?limit=20');
            const data = await response.json();
            this.displayEmployees(data.employees || []);
            
        } catch (error) {
            console.error('Error loading employees:', error);
            this.showNotification('Error loading employees', 'error');
        }
    }

    displayEmployees(employees) {
        const employeesGrid = document.getElementById('employeesGrid');
        if (!employeesGrid) return;

        if (employees.length === 0) {
            employeesGrid.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-users"></i>
                    <p>No employees found</p>
                </div>
            `;
            return;
        }

        employeesGrid.innerHTML = employees.map(employee => `
            <div class="employee-card">
                <div class="employee-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="employee-info">
                    <h4>${employee.full_name || 'Unknown'}</h4>
                    <p>${employee.role || 'Unknown Role'}</p>
                    <span class="employee-department">${employee.department || 'Unknown'}</span>
                </div>
                <div class="employee-actions">
                    <button class="btn-icon" onclick="dashboard.viewEmployee('${employee.employee_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    formatAIResponse(response) {
        // Convert the AI response to HTML with professional styling
        let formattedResponse = response;
        
        // Add executive summary styling
        formattedResponse = formattedResponse.replace(
            /EXECUTIVE SUMMARY[:\s]*(.*?)(?=KEY FINDINGS|STRATEGIC IMPLICATIONS|RECOMMENDED ACTIONS|$)/is,
            '<div class="executive-summary"><h3>📊 Executive Summary</h3><p>$1</p></div>'
        );
        
        // Add key findings styling
        formattedResponse = formattedResponse.replace(
            /KEY FINDINGS[:\s]*(.*?)(?=STRATEGIC IMPLICATIONS|RECOMMENDED ACTIONS|DETAILED ANALYSIS|$)/is,
            '<div class="key-findings"><h3>🔍 Key Findings</h3>$1</div>'
        );
        
        // Add strategic implications styling
        formattedResponse = formattedResponse.replace(
            /STRATEGIC IMPLICATIONS[:\s]*(.*?)(?=RECOMMENDED ACTIONS|$)/is,
            '<div class="strategic-implications"><h3>💼 Strategic Implications</h3>$1</div>'
        );
        
        // Add recommended actions styling
        formattedResponse = formattedResponse.replace(
            /RECOMMENDED ACTIONS[:\s]*(.*?)$/is,
            '<div class="recommended-actions"><h3>🎯 Recommended Actions</h3>$1</div>'
        );
        
        // Convert bullet points to proper HTML
        formattedResponse = formattedResponse.replace(/•\s*(.*?)(?=\n|$)/g, '<li>$1</li>');
        formattedResponse = formattedResponse.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Convert numbered lists
        formattedResponse = formattedResponse.replace(/(\d+\.\s*.*?)(?=\n\d+\.|\n\n|$)/g, '<li>$1</li>');
        
        // Convert markdown tables to HTML
        formattedResponse = formattedResponse.replace(
            /\|(.+?)\|\n\|[-\s|]+\|\n((?:\|.*\|\n?)*)/g,
            (match, header, rows) => {
                const headers = header.split('|').map(h => h.trim()).filter(h => h);
                const rowData = rows.split('\n').filter(row => row.trim()).map(row => 
                    row.split('|').map(cell => cell.trim()).filter(cell => cell)
                );
                
                let table = '<table><thead><tr>';
                headers.forEach(h => table += `<th>${h}</th>`);
                table += '</tr></thead><tbody>';
                
                rowData.forEach(row => {
                    table += '<tr>';
                    row.forEach(cell => table += `<td>${cell}</td>`);
                    table += '</tr>';
                });
                
                table += '</tbody></table>';
                return table;
            }
        );
        
        // Enhanced formatting for AI Analytics responses
        formattedResponse = this.enhanceAnalyticsFormatting(formattedResponse);
        
        // Convert line breaks to HTML
        formattedResponse = formattedResponse.replace(/\n\n/g, '</p><p>');
        formattedResponse = formattedResponse.replace(/\n/g, '<br>');
        
        // Wrap in paragraph tags
        formattedResponse = `<p>${formattedResponse}</p>`;
        
        return formattedResponse;
    }

    enhanceAnalyticsFormatting(text) {
        // Enhanced formatting for executive-ready analytics
        return text
            // Format prediction tables
            .replace(/Prediction\s+Insight\s+Confidence\s+Key Drivers/g, 
                '<table class="ai-analytics-table"><thead><tr><th class="ai-table-header">Prediction</th><th class="ai-table-header">Insight</th><th class="ai-table-header">Confidence</th><th class="ai-table-header">Key Drivers</th></tr></thead><tbody>')
            
            // Format risk assessment tables
            .replace(/Risk Category\s+🔍 Key Findings\s+Likelihood\s+Impact\s+Risk Score.*?Mitigation Priority/g, 
                '<table class="ai-risk-table"><thead><tr><th class="ai-table-header">Risk Category</th><th class="ai-table-header">Key Findings</th><th class="ai-table-header">Likelihood</th><th class="ai-table-header">Impact</th><th class="ai-table-header">Risk Score</th><th class="ai-table-header">Mitigation Priority</th></tr></thead><tbody>')
            
            // Format workforce optimization tables
            .replace(/#\s+Focus Area\s+Key Insight\s+Actionable Initiative\s+Expected Impact\s+ROI Estimate/g, 
                '<table class="ai-workforce-table"><thead><tr><th class="ai-table-header">#</th><th class="ai-table-header">Focus Area</th><th class="ai-table-header">Key Insight</th><th class="ai-table-header">Actionable Initiative</th><th class="ai-table-header">Expected Impact</th><th class="ai-table-header">ROI Estimate</th></tr></thead><tbody>')
            
            // Format confidence levels
            .replace(/\*\*(High|Medium|Low)\*\*/g, '<span class="confidence-level $1">$1</span>')
            
            // Format risk levels
            .replace(/\*\*(Low|Medium|High|Critical)\*\*/g, '<span class="risk-level $1">$1</span>')
            
            // Format percentages
            .replace(/(\d+)\s*%/g, '<span class="percentage">$1%</span>')
            
            // Format key metrics
            .replace(/(\d+)\s*(employees|departments|courses|days)/g, '<span class="metric-value">$1</span> <span class="metric-unit">$2</span>')
            
            // Format executive summary sections
            .replace(/\*\*Executive Summary\*\*/g, '<div class="executive-summary"><h3 class="ai-h3">Executive Summary</h3>')
            .replace(/\*\*Key Findings\*\*/g, '<div class="key-findings"><h3 class="ai-h3">Key Findings</h3>')
            .replace(/\*\*Strategic Implications\*\*/g, '<div class="strategic-implications"><h3 class="ai-h3">Strategic Implications</h3>')
            .replace(/\*\*Recommended Actions\*\*/g, '<div class="recommended-actions"><h3 class="ai-h3">Recommended Actions</h3>')
            
            // Format data snapshots
            .replace(/\*Data snapshot:([^*]+)\*/g, '<div class="data-snapshot"><i class="fas fa-database"></i> Data Snapshot: $1</div>')
            
            // Format risk scores
            .replace(/(\d+)\s*×\s*(\d+)\s*=\s*(\d+)/g, '<span class="risk-calculation">$1 × $2 = <strong>$3</strong></span>')
            
            // Format ROI estimates
            .replace(/ROI Estimate:?\s*([^<]+)/g, '<div class="roi-estimate"><i class="fas fa-chart-line"></i> ROI Estimate: <strong>$1</strong></div>')
            
            // Format section headers
            .replace(/\*\*([^*]+)\*\*/g, '<h4 class="ai-section-header">$1</h4>')
            
            // Format bullet points with better styling
            .replace(/•\s*(.*?)(?=\n|$)/g, '<li class="ai-bullet-point">$1</li>')
            
            // Format numbered items
            .replace(/(\d+)\.\s*(.*?)(?=\n\d+\.|\n\n|$)/g, '<li class="ai-numbered-point">$1. $2</li>')
            
            // Format emphasis
            .replace(/\*([^*]+)\*/g, '<em class="ai-emphasis">$1</em>');
    }
    }

    async searchEmployees(query) {
        if (!query.trim()) {
            await this.loadEmployees();
            return;
        }

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 20
                })
            });

            const data = await response.json();
            this.displayEmployees(data.employees || []);
            
        } catch (error) {
            console.error('Error searching employees:', error);
        }
    }

    async loadAnalyticsData() {
        try {
            this.showLoading(true);
            
            // Load all analytics data in parallel
            const [departments, performance, salary, attrition] = await Promise.all([
                fetch('/api/analytics/departments').then(r => r.json()),
                fetch('/api/analytics/performance').then(r => r.json()),
                fetch('/api/analytics/salary').then(r => r.json()),
                fetch('/api/analytics/attrition').then(r => r.json())
            ]);
            
            this.displayAnalyticsData({ departments, performance, salary, attrition });
            
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showNotification('Error loading analytics data', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadAdvancedAnalytics() {
        try {
            this.showLoading(true);
            
            // Load advanced AI-powered analytics
            const [executiveDashboard, predictiveInsights, talentIntelligence, workforceOptimization, riskAssessment] = await Promise.all([
                fetch('/api/analytics/executive-dashboard').then(r => r.json()),
                fetch('/api/analytics/predictive-insights').then(r => r.json()),
                fetch('/api/analytics/talent-intelligence').then(r => r.json()),
                fetch('/api/analytics/workforce-optimization').then(r => r.json()),
                fetch('/api/analytics/risk-assessment').then(r => r.json())
            ]);
            
            this.displayAdvancedAnalytics({
                executiveDashboard,
                predictiveInsights,
                talentIntelligence,
                workforceOptimization,
                riskAssessment
            });
            
        } catch (error) {
            console.error('Error loading advanced analytics:', error);
            this.showNotification('Error loading advanced analytics', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayAnalyticsData(data) {
        const analyticsContainer = document.getElementById('analyticsContent');
        if (!analyticsContainer) return;

        analyticsContainer.innerHTML = `
            <div class="analytics-grid">
                <!-- Department Analytics -->
                <div class="analytics-card">
                    <div class="card-header">
                        <h3><i class="fas fa-building"></i> Department Analytics</h3>
                    </div>
                    <div class="card-content">
                        <div class="metric-summary">
                            <div class="metric">
                                <span class="metric-value">${data.departments.total_departments}</span>
                                <span class="metric-label">Departments</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value">${data.departments.total_employees}</span>
                                <span class="metric-label">Total Employees</span>
                            </div>
                        </div>
                        <div class="department-list">
                            ${data.departments.departments.map(dept => `
                                <div class="department-item">
                                    <div class="dept-info">
                                        <span class="dept-name">${dept.department}</span>
                                        <span class="dept-count">${dept.employee_count} employees</span>
                                    </div>
                                    <div class="dept-metrics">
                                        <span class="metric">Performance: ${dept.avg_performance}/5</span>
                                        <span class="metric">KPIs: ${dept.avg_kpis}%</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Performance Analytics -->
                <div class="analytics-card">
                    <div class="card-header">
                        <h3><i class="fas fa-chart-line"></i> Performance Analytics</h3>
                    </div>
                    <div class="card-content">
                        <div class="metric-summary">
                            <div class="metric">
                                <span class="metric-value">${data.performance.avg_performance}</span>
                                <span class="metric-label">Avg Rating</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value">${data.performance.high_performer_pct}%</span>
                                <span class="metric-label">High Performers</span>
                            </div>
                        </div>
                        <div class="performance-breakdown">
                            <div class="perf-item high">
                                <span class="perf-label">High Performers (4.0+)</span>
                                <span class="perf-count">${data.performance.high_performers} (${data.performance.high_performer_pct}%)</span>
                            </div>
                            <div class="perf-item medium">
                                <span class="perf-label">Medium Performers (3.0-3.9)</span>
                                <span class="perf-count">${data.performance.total_employees - data.performance.high_performers - data.performance.low_performers}</span>
                            </div>
                            <div class="perf-item low">
                                <span class="perf-label">Low Performers (<3.0)</span>
                                <span class="perf-count">${data.performance.low_performers} (${data.performance.low_performer_pct}%)</span>
                            </div>
                        </div>
                        <div class="performance-range">
                            <span>Range: ${data.performance.min_performance} - ${data.performance.max_performance}</span>
                            <span>Avg KPIs: ${data.performance.avg_kpis}%</span>
                        </div>
                    </div>
                </div>

                <!-- Salary Analytics -->
                <div class="analytics-card">
                    <div class="card-header">
                        <h3><i class="fas fa-dollar-sign"></i> Salary Analytics</h3>
                    </div>
                    <div class="card-content">
                        <div class="metric-summary">
                            <div class="metric">
                                <span class="metric-value">$${data.salary.avg_salary.toLocaleString()}</span>
                                <span class="metric-label">Avg Salary</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value">$${data.salary.salary_range.toLocaleString()}</span>
                                <span class="metric-label">Salary Range</span>
                            </div>
                        </div>
                        <div class="salary-range">
                            <span>Min: $${data.salary.min_salary.toLocaleString()}</span>
                            <span>Max: $${data.salary.max_salary.toLocaleString()}</span>
                        </div>
                        <div class="department-salaries">
                            <h4>By Department:</h4>
                            ${data.salary.department_analytics.map(dept => `
                                <div class="dept-salary">
                                    <span class="dept-name">${dept.department}</span>
                                    <span class="salary-info">
                                        $${dept.avg_salary.toLocaleString()} (${dept.employee_count} employees)
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Attrition Analytics -->
                <div class="analytics-card">
                    <div class="card-header">
                        <h3><i class="fas fa-exclamation-triangle"></i> Attrition Risk Analytics</h3>
                    </div>
                    <div class="card-content">
                        <div class="metric-summary">
                            <div class="metric">
                                <span class="metric-value">${data.attrition.avg_risk_score}</span>
                                <span class="metric-label">Avg Risk Score</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value">${data.attrition.high_risk_pct}%</span>
                                <span class="metric-label">High Risk</span>
                            </div>
                        </div>
                        <div class="risk-breakdown">
                            <div class="risk-item high">
                                <span class="risk-label">High Risk (7+)</span>
                                <span class="risk-count">${data.attrition.high_risk} (${data.attrition.high_risk_pct}%)</span>
                            </div>
                            <div class="risk-item medium">
                                <span class="risk-label">Medium Risk (4-6)</span>
                                <span class="risk-count">${data.attrition.medium_risk} (${data.attrition.medium_risk_pct}%)</span>
                            </div>
                            <div class="risk-item low">
                                <span class="risk-label">Low Risk (<4)</span>
                                <span class="risk-count">${data.attrition.low_risk} (${data.attrition.low_risk_pct}%)</span>
                            </div>
                        </div>
                        <div class="department-risks">
                            <h4>Risk by Department:</h4>
                            ${data.attrition.department_analytics.map(dept => `
                                <div class="dept-risk">
                                    <span class="dept-name">${dept.department}</span>
                                    <span class="risk-info">
                                        Risk: ${dept.avg_risk} (${dept.high_risk_count} high risk)
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    displayAdvancedAnalytics(data) {
        const analyticsContainer = document.getElementById('analyticsContent');
        if (!analyticsContainer) return;

        analyticsContainer.innerHTML = `
            <div class="advanced-analytics-grid">
                <!-- Executive Dashboard -->
                <div class="analytics-card executive-card">
                    <div class="card-header">
                        <h3><i class="fas fa-chart-line"></i> Executive Dashboard</h3>
                    </div>
                    <div class="card-content">
                        <div class="ai-insights">
                            <h4>AI-Powered Insights</h4>
                            <div class="insight-content">
                                ${this.formatAIResponse(data.executiveDashboard.ai_insights?.analysis || 'Loading insights...')}
                            </div>
                        </div>
                        <div class="recommendations">
                            <h4>Strategic Recommendations</h4>
                            <div class="recommendation-list">
                                ${data.executiveDashboard.recommendations?.map(rec => `
                                    <div class="recommendation-item ${rec.priority.toLowerCase()}">
                                        <span class="rec-category">${rec.category}</span>
                                        <span class="rec-title">${rec.title}</span>
                                        <span class="rec-action">${rec.action}</span>
                                    </div>
                                `).join('') || 'Loading recommendations...'}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Predictive Insights -->
                <div class="analytics-card predictive-card">
                    <div class="card-header">
                        <h3><i class="fas fa-crystal-ball"></i> Predictive Insights</h3>
                    </div>
                    <div class="card-content">
                        <div class="prediction-content">
                            <div class="confidence-badge ${data.predictiveInsights.confidence_level?.toLowerCase()}">
                                ${data.predictiveInsights.confidence_level || 'High'} Confidence
                            </div>
                            <div class="ai-predictions">
                                ${this.formatAIResponse(data.predictiveInsights.predictions || 'Generating predictions...')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Talent Intelligence -->
                <div class="analytics-card talent-card">
                    <div class="card-header">
                        <h3><i class="fas fa-users"></i> Talent Intelligence</h3>
                    </div>
                    <div class="card-content">
                        <div class="talent-content">
                            <div class="analysis-type">${data.talentIntelligence.analysis_type || 'Comprehensive Talent Assessment'}</div>
                            <div class="ai-talent-analysis">
                                ${this.formatAIResponse(data.talentIntelligence.talent_intelligence || 'Analyzing talent...')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Workforce Optimization -->
                <div class="analytics-card optimization-card">
                    <div class="card-header">
                        <h3><i class="fas fa-cogs"></i> Workforce Optimization</h3>
                    </div>
                    <div class="card-content">
                        <div class="optimization-content">
                            <div class="timeline-badge">${data.workforceOptimization.implementation_timeline || '90 days'}</div>
                            <div class="focus-areas">
                                ${data.workforceOptimization.focus_areas?.map(area => `
                                    <span class="focus-area">${area}</span>
                                `).join('') || ''}
                            </div>
                            <div class="ai-optimization-plan">
                                ${this.formatAIResponse(data.workforceOptimization.optimization_plan || 'Generating optimization plan...')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Risk Assessment -->
                <div class="analytics-card risk-card">
                    <div class="card-header">
                        <h3><i class="fas fa-shield-alt"></i> Risk Assessment</h3>
                    </div>
                    <div class="card-content">
                        <div class="risk-content">
                            <div class="risk-levels">
                                ${data.riskAssessment.risk_levels?.map(level => `
                                    <span class="risk-level ${level.toLowerCase()}">${level}</span>
                                `).join('') || ''}
                            </div>
                            <div class="ai-risk-assessment">
                                ${this.formatAIResponse(data.riskAssessment.risk_assessment || 'Assessing risks...')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AI Agent Status -->
                <div class="analytics-card agent-card">
                    <div class="card-header">
                        <h3><i class="fas fa-robot"></i> AI Agent Status</h3>
                    </div>
                    <div class="card-content">
                        <div class="agent-status">
                            <div class="status-item">
                                <span class="status-label">Analytics Agent:</span>
                                <span class="status-value active">Active</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Predictive Engine:</span>
                                <span class="status-value active">Active</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Talent Intelligence:</span>
                                <span class="status-value active">Active</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Risk Assessment:</span>
                                <span class="status-value active">Active</span>
                            </div>
                            <div class="status-item">
                                <span class="status-label">Last Update:</span>
                                <span class="status-value">${new Date().toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadReportsData() {
        // Placeholder for reports data loading
        console.log('Loading reports data...');
    }

    async submitQuery() {
        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();

        if (!query) {
            this.showNotification('Please enter a query', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 5
                })
            });

            const data = await response.json();
            this.displayQueryResults(data);
            
            // Clear input
            queryInput.value = '';
            
        } catch (error) {
            console.error('Error submitting query:', error);
            this.showNotification('Error processing query', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayQueryResults(data) {
        const resultsContainer = document.getElementById('queryResults');
        if (!resultsContainer) return;

        const responseTime = data.response_time ? ` (${data.response_time.toFixed(2)}s)` : '';
        
        // Format the AI response with professional styling
        const formattedResponse = this.formatAIResponse(data.response);
        
        resultsContainer.innerHTML = `
            <div class="query-result">
                <div class="result-header">
                    <h4>Executive Analysis: "${data.query}"</h4>
                    <div class="result-meta">
                        <span class="intent-badge">${data.intent.replace('_', ' ').toUpperCase()}</span>
                        <span class="response-time">${responseTime}</span>
                    </div>
                </div>
                <div class="ai-response">
                    ${formattedResponse}
                </div>
                ${data.search_results && data.search_results.length > 0 ? `
                    <div class="result-data">
                        <h5>Data Sources:</h5>
                        <div class="data-items">
                            ${data.search_results.slice(0, 3).map(result => `
                                <div class="data-item">
                                    <strong>${result.full_name || result.employee_id || 'Employee'}</strong>
                                    <span>${result.department || 'Unknown Department'}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        // Add CSS for result styling
        if (!document.getElementById('query-result-styles')) {
            const style = document.createElement('style');
            style.id = 'query-result-styles';
            style.textContent = `
                .query-result {
                    animation: fadeIn 0.3s ease;
                }
                .result-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid var(--border-color);
                }
                .result-header h4 {
                    color: var(--text-primary);
                    font-weight: 600;
                }
                .result-meta {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }
                .intent-badge {
                    background: var(--primary-color);
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: var(--radius-sm);
                    font-size: 0.75rem;
                    font-weight: 500;
                }
                .response-time {
                    color: var(--text-muted);
                    font-size: 0.875rem;
                }
                .result-content {
                    margin-bottom: 1.5rem;
                }
                .result-content p {
                    color: var(--text-primary);
                    line-height: 1.6;
                }
                .result-data h5 {
                    color: var(--text-primary);
                    font-weight: 600;
                    margin-bottom: 1rem;
                }
                .data-items {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }
                .data-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-md);
                }
                .data-item strong {
                    color: var(--text-primary);
                }
                .data-item span {
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                }
            `;
            document.head.appendChild(style);
        }
    }

    setQuery(query) {
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.value = query;
            queryInput.focus();
        }
    }

    async viewEmployee(employeeId) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/employee/${employeeId}`);
            const employee = await response.json();
            
            this.hideLoading();
            this.showEmployeeModal(employee);
            
        } catch (error) {
            this.hideLoading();
            console.error('Error loading employee details:', error);
            this.showNotification('Error loading employee details', 'error');
        }
    }

    showEmployeeModal(employee) {
        // Create modal HTML
        const modalHTML = `
            <div class="modal-overlay" onclick="dashboard.closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h2>Employee Details</h2>
                        <button class="modal-close" onclick="dashboard.closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="employee-detail-grid">
                            <div class="detail-section">
                                <h3><i class="fas fa-user"></i> Personal Information</h3>
                                <div class="detail-row">
                                    <span class="label">Name:</span>
                                    <span class="value">${employee.full_name || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Employee ID:</span>
                                    <span class="value">${employee.employee_id || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Email:</span>
                                    <span class="value">${employee.email || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Age:</span>
                                    <span class="value">${employee.age || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Gender:</span>
                                    <span class="value">${employee.gender || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Location:</span>
                                    <span class="value">${employee.location || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Contact:</span>
                                    <span class="value">${employee.contact_number || 'N/A'}</span>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3><i class="fas fa-briefcase"></i> Employment Details</h3>
                                <div class="detail-row">
                                    <span class="label">Department:</span>
                                    <span class="value">${employee.employment?.department || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Role:</span>
                                    <span class="value">${employee.employment?.role || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Manager:</span>
                                    <span class="value">${employee.employment?.manager || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Date of Joining:</span>
                                    <span class="value">${employee.employment?.date_of_joining || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Grade/Band:</span>
                                    <span class="value">${employee.employment?.grade || 'N/A'}</span>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3><i class="fas fa-chart-line"></i> Performance</h3>
                                <div class="detail-row">
                                    <span class="label">Performance Rating:</span>
                                    <span class="value">${employee.performance?.performance_rating || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">KPIs Met:</span>
                                    <span class="value">${employee.performance?.kpis_met_pct || 'N/A'}%</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Awards:</span>
                                    <span class="value">${employee.performance?.awards || 'None'}</span>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3><i class="fas fa-dollar-sign"></i> Compensation</h3>
                                <div class="detail-row">
                                    <span class="label">Current Salary:</span>
                                    <span class="value">$${employee.compensation?.current_salary?.toLocaleString() || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Bonus History:</span>
                                    <span class="value">$${employee.compensation?.bonus_history || 'N/A'}</span>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3><i class="fas fa-calendar-check"></i> Attendance</h3>
                                <div class="detail-row">
                                    <span class="label">Monthly Attendance:</span>
                                    <span class="value">${employee.attendance?.monthly_attendance_pct || 'N/A'}%</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Leave Pattern:</span>
                                    <span class="value">${employee.attendance?.leave_pattern || 'N/A'}</span>
                                </div>
                            </div>
                            
                            <div class="detail-section">
                                <h3><i class="fas fa-graduation-cap"></i> Learning & Development</h3>
                                <div class="detail-row">
                                    <span class="label">Courses Completed:</span>
                                    <span class="value">${employee.learning?.courses_completed || 'N/A'}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="label">Certifications:</span>
                                    <span class="value">${employee.learning?.certifications || 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        // Simulate connection check
        setTimeout(() => {
            statusElement.innerHTML = `
                <i class="fas fa-circle" style="color: #10b981;"></i>
                Connected
            `;
            statusElement.className = 'status-indicator connected';
        }, 2000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.add('active');
            } else {
                overlay.classList.remove('active');
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;

        // Add notification styles if not already added
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 2rem;
                    right: 2rem;
                    background: var(--bg-primary);
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-lg);
                    padding: 1rem 1.5rem;
                    box-shadow: var(--shadow-lg);
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    z-index: 10000;
                    animation: slideInRight 0.3s ease;
                }
                .notification-info {
                    border-left: 4px solid var(--primary-color);
                }
                .notification-success {
                    border-left: 4px solid var(--success-color);
                }
                .notification-warning {
                    border-left: 4px solid var(--warning-color);
                }
                .notification-error {
                    border-left: 4px solid var(--danger-color);
                }
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        const icons = {
            info: 'info-circle',
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Global functions for HTML onclick handlers
function showSection(sectionName) {
    if (window.dashboard) {
        window.dashboard.showSection(sectionName);
    }
}

function setQuery(query) {
    if (window.dashboard) {
        window.dashboard.setQuery(query);
    }
}

function submitQuery() {
    if (window.dashboard) {
        window.dashboard.submitQuery();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new HRAnalyticsDashboard();
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    // Handle responsive adjustments if needed
});

// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus query input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.focus();
        }
    }
    
    // Escape to close modals/overlays
    if (e.key === 'Escape') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay && overlay.classList.contains('active')) {
            overlay.classList.remove('active');
        }
    }
});

// Add Employee Modal Functions
function showAddEmployeeModal() {
    const modal = document.getElementById('addEmployeeModal');
    modal.style.display = 'block';
}

function closeAddEmployeeModal() {
    const modal = document.getElementById('addEmployeeModal');
    modal.style.display = 'none';
    document.getElementById('addEmployeeForm').reset();
}

// Handle Add Employee Form Submission
document.getElementById('addEmployeeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const employeeData = Object.fromEntries(formData.entries());
    
    // Convert numeric fields
    if (employeeData.current_salary) {
        employeeData.current_salary = parseFloat(employeeData.current_salary);
    }
    if (employeeData.age) {
        employeeData.age = parseInt(employeeData.age);
    }
    
    try {
        const response = await fetch('/api/employee', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(employeeData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`Employee ${result.employee_id} added successfully!`, 'success');
            closeAddEmployeeModal();
            
            // Refresh employee list if we're on the employees page
            if (document.getElementById('employeesGrid')) {
                await dashboard.loadEmployees();
            }
            
            // Refresh analytics if we're on analytics page
            if (document.getElementById('analyticsContent')) {
                await dashboard.loadAnalyticsData();
            }
        } else {
            const error = await response.json();
            showNotification(`Error: ${error.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Error adding employee: ${error.message}`, 'error');
    }
});

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('addEmployeeModal');
    if (event.target === modal) {
        closeAddEmployeeModal();
    }
});
