// HR Q&A System - Frontend Application
class HRAnalyticsApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentPage = 1;
        this.pageSize = 12;
        this.currentFilters = {};
        this.recentQueries = JSON.parse(localStorage.getItem('recentQueries') || '[]');
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkConnection();
        await this.loadDashboardData();
        this.loadRecentQueries();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.showSection(section);
            });
        });

        // Query submission
        document.getElementById('submitQuery').addEventListener('click', () => {
            this.submitQuery();
        });

        document.getElementById('queryInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.submitQuery();
            }
        });

        // Employee filters
        document.getElementById('applyFilters').addEventListener('click', () => {
            this.applyEmployeeFilters();
        });

        // Pagination
        document.getElementById('prevPage').addEventListener('click', () => {
            this.changePage(this.currentPage - 1);
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            this.changePage(this.currentPage + 1);
        });

        // Search input
        document.getElementById('searchInput').addEventListener('input', (e) => {
            if (e.target.value.length > 2) {
                this.debounceSearch();
            }
        });
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            const statusElement = document.getElementById('connectionStatus');
            if (data.status === 'healthy') {
                statusElement.className = 'status-indicator connected';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
            } else {
                statusElement.className = 'status-indicator error';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Error';
            }
        } catch (error) {
            const statusElement = document.getElementById('connectionStatus');
            statusElement.className = 'status-indicator error';
            statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
        }
    }

    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Show section
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        // Load section-specific data
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
            case 'employees':
                this.loadEmployees();
                break;
        }
    }

    async loadDashboardData() {
        try {
            this.showLoading();
            
            // Load overview analytics
            const response = await fetch(`${this.apiBaseUrl}/analytics/overview`);
            const data = await response.json();
            
            // Update stats cards
            document.getElementById('totalEmployees').textContent = data.total_employees || 0;
            document.getElementById('totalDepartments').textContent = data.total_departments || 0;
            document.getElementById('totalRoles').textContent = data.total_roles || 0;
            
            // Calculate average performance if available
            if (data.top_roles && Object.keys(data.top_roles).length > 0) {
                document.getElementById('avgPerformance').textContent = '4.2'; // Placeholder
            } else {
                document.getElementById('avgPerformance').textContent = '-';
            }
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async submitQuery() {
        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();
        
        if (!query) {
            this.showToast('Please enter a query', 'warning');
            return;
        }

        try {
            this.showLoading();
            
            const response = await fetch(`${this.apiBaseUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 10
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayQueryResults(data);
                this.addToRecentQueries(query);
            } else {
                this.showToast(data.error || 'Query failed', 'error');
            }
            
        } catch (error) {
            console.error('Query failed:', error);
            this.showToast('Query failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayQueryResults(data) {
        const resultsContainer = document.getElementById('queryResults');
        const resultsContent = document.getElementById('resultsContent');
        const queryIntent = document.getElementById('queryIntent');
        const queryTime = document.getElementById('queryTime');
        
        // Show results container
        resultsContainer.style.display = 'block';
        
        // Update metadata
        queryIntent.textContent = `Intent: ${data.intent}`;
        queryTime.textContent = `Time: ${data.processing_time_ms?.toFixed(0) || 0}ms`;
        
        // Display results based on query type
        let html = '';
        
        if (data.intent === 'count_query') {
            html = `<div class="result-summary">
                <h4>Query Result</h4>
                <p class="result-text">${data.response}</p>
                <div class="result-count">
                    <span class="count-number">${data.count}</span>
                    <span class="count-label">employees found</span>
                </div>
            </div>`;
        } else if (data.intent === 'comparison') {
            html = `<div class="result-summary">
                <h4>Comparison Results</h4>
                <p class="result-text">${data.response}</p>
                <div class="comparison-data">`;
            
            if (data.results && data.results.length > 0) {
                data.results.forEach(result => {
                    html += `<div class="comparison-item">
                        <h5>${result._id || 'Unknown'}</h5>
                        <div class="comparison-stats">
                            <span>Count: ${result.count || 0}</span>
                            ${result.avg_salary ? `<span>Avg Salary: $${result.avg_salary.toLocaleString()}</span>` : ''}
                            ${result.avg_rating ? `<span>Avg Rating: ${result.avg_rating.toFixed(1)}</span>` : ''}
                        </div>
                    </div>`;
                });
            }
            
            html += `</div></div>`;
        } else if (data.intent === 'ranking') {
            html = `<div class="result-summary">
                <h4>Ranking Results</h4>
                <p class="result-text">${data.response}</p>
                <div class="ranking-list">`;
            
            if (data.results && data.results.length > 0) {
                data.results.forEach((result, index) => {
                    html += `<div class="ranking-item">
                        <span class="rank">${index + 1}</span>
                        <div class="employee-info">
                            <h5>${result.full_name || 'Unknown'}</h5>
                            <p>${result.department || 'N/A'} - ${result.role || 'N/A'}</p>
                            ${result.performance_rating ? `<span class="rating">Rating: ${result.performance_rating}</span>` : ''}
                            ${result.salary ? `<span class="salary">Salary: $${result.salary.toLocaleString()}</span>` : ''}
                        </div>
                    </div>`;
                });
            }
            
            html += `</div></div>`;
        } else {
            html = `<div class="result-summary">
                <h4>Query Results</h4>
                <p class="result-text">${data.response}</p>
                <div class="result-count">
                    <span class="count-number">${data.count}</span>
                    <span class="count-label">employees found</span>
                </div>
            </div>`;
        }
        
        resultsContent.innerHTML = html;
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    addToRecentQueries(query) {
        // Add to recent queries (max 5)
        this.recentQueries = [query, ...this.recentQueries.filter(q => q !== query)].slice(0, 5);
        localStorage.setItem('recentQueries', JSON.stringify(this.recentQueries));
        this.loadRecentQueries();
    }

    loadRecentQueries() {
        const container = document.getElementById('recentQueries');
        
        if (this.recentQueries.length === 0) {
            container.innerHTML = '<div class="activity-item"><i class="fas fa-search"></i><span>No recent queries</span></div>';
            return;
        }
        
        container.innerHTML = this.recentQueries.map(query => 
            `<div class="activity-item" onclick="setQuery('${query}')">
                <i class="fas fa-search"></i>
                <span>${query}</span>
            </div>`
        ).join('');
    }

    async loadAnalyticsData() {
        try {
            this.showLoading();
            
            // Load department analytics
            const deptResponse = await fetch(`${this.apiBaseUrl}/analytics/departments`);
            const deptData = await deptResponse.json();
            
            // Load position analytics
            const posResponse = await fetch(`${this.apiBaseUrl}/analytics/positions`);
            const posData = await posResponse.json();
            
            // Update charts
            this.updateDepartmentChart(deptData.departments || []);
            this.updateRoleChart(posData.positions || []);
            
            // Update performance stats
            document.getElementById('avgRating').textContent = '4.2'; // Placeholder
            document.getElementById('topPerformers').textContent = '15'; // Placeholder
            
        } catch (error) {
            console.error('Failed to load analytics data:', error);
            this.showToast('Failed to load analytics data', 'error');
        } finally {
            this.hideLoading();
        }
    }

    updateDepartmentChart(departments) {
        const ctx = document.getElementById('departmentChart').getContext('2d');
        
        if (window.departmentChart) {
            window.departmentChart.destroy();
        }
        
        window.departmentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: departments.map(d => d.department),
                datasets: [{
                    data: departments.map(d => d.count),
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#f5576c',
                        '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    updateRoleChart(roles) {
        const ctx = document.getElementById('roleChart').getContext('2d');
        
        if (window.roleChart) {
            window.roleChart.destroy();
        }
        
        window.roleChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: roles.map(r => r.position),
                datasets: [{
                    label: 'Employees',
                    data: roles.map(r => r.count),
                    backgroundColor: '#4f46e5',
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f3f4f6'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    async loadEmployees() {
        try {
            this.showLoading();
            
            // Load employees with current filters and pagination
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize,
                ...this.currentFilters
            });
            
            const response = await fetch(`${this.apiBaseUrl}/search/employees?${params}`);
            const data = await response.json();
            
            this.displayEmployees(data.employees || []);
            this.updatePagination(data.total_count || 0);
            
            // Load filter options
            await this.loadFilterOptions();
            
        } catch (error) {
            console.error('Failed to load employees:', error);
            this.showToast('Failed to load employees', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayEmployees(employees) {
        const container = document.getElementById('employeeGrid');
        
        if (employees.length === 0) {
            container.innerHTML = '<div class="loading-state"><i class="fas fa-users"></i><span>No employees found</span></div>';
            return;
        }
        
        container.innerHTML = employees.map(emp => `
            <div class="employee-card">
                <div class="employee-header">
                    <div class="employee-avatar">
                        ${emp.full_name ? emp.full_name.charAt(0).toUpperCase() : '?'}
                    </div>
                    <div class="employee-info">
                        <h4>${emp.full_name || 'Unknown'}</h4>
                        <p>${emp.employee_id || 'N/A'}</p>
                    </div>
                </div>
                <div class="employee-details">
                    <div class="employee-detail">
                        <span>Department:</span>
                        <span>${emp.department || 'N/A'}</span>
                    </div>
                    <div class="employee-detail">
                        <span>Role:</span>
                        <span>${emp.role || 'N/A'}</span>
                    </div>
                    <div class="employee-detail">
                        <span>Location:</span>
                        <span>${emp.location || 'N/A'}</span>
                    </div>
                    ${emp.certifications ? `
                    <div class="employee-detail">
                        <span>Certifications:</span>
                        <span>${emp.certifications}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    async loadFilterOptions() {
        try {
            // Load departments
            const deptResponse = await fetch(`${this.apiBaseUrl}/analytics/departments`);
            const deptData = await deptResponse.json();
            
            const deptSelect = document.getElementById('deptFilter');
            deptSelect.innerHTML = '<option value="">All Departments</option>' +
                (deptData.departments || []).map(d => 
                    `<option value="${d.department}">${d.department} (${d.count})</option>`
                ).join('');
            
            // Load roles
            const roleResponse = await fetch(`${this.apiBaseUrl}/analytics/positions`);
            const roleData = await roleResponse.json();
            
            const roleSelect = document.getElementById('roleFilter');
            roleSelect.innerHTML = '<option value="">All Roles</option>' +
                (roleData.positions || []).map(r => 
                    `<option value="${r.position}">${r.position} (${r.count})</option>`
                ).join('');
                
        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    }

    applyEmployeeFilters() {
        this.currentFilters = {
            department: document.getElementById('deptFilter').value,
            position: document.getElementById('roleFilter').value,
            search: document.getElementById('searchInput').value
        };
        
        // Remove empty filters
        Object.keys(this.currentFilters).forEach(key => {
            if (!this.currentFilters[key]) {
                delete this.currentFilters[key];
            }
        });
        
        this.currentPage = 1;
        this.loadEmployees();
    }

    changePage(page) {
        this.currentPage = page;
        this.loadEmployees();
    }

    updatePagination(totalCount) {
        const totalPages = Math.ceil(totalCount / this.pageSize);
        const pagination = document.getElementById('pagination');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');
        
        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }
        
        pagination.style.display = 'flex';
        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= totalPages;
        pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
    }

    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.applyEmployeeFilters();
        }, 500);
    }

    showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    async runSampleQueries() {
        const sampleQueries = [
            "How many employees work in IT department?",
            "Show me developers with AWS certification",
            "Top 5 performers in the company",
            "Compare average salary between IT and Sales"
        ];
        
        this.showSection('query');
        
        for (let i = 0; i < sampleQueries.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            document.getElementById('queryInput').value = sampleQueries[i];
            await this.submitQuery();
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}

// Global functions
function setQuery(query) {
    document.getElementById('queryInput').value = query;
    document.getElementById('queryInput').focus();
}

function showSection(section) {
    window.app.showSection(section);
}

function runSampleQueries() {
    window.app.runSampleQueries();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new HRAnalyticsApp();
});
