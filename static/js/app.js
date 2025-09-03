/**
 * Bilibili视频分析系统 - 全局JavaScript
 */

// 应用状态管理
const AppState = {
    // 用户设置
    settings: {
        theme: 'light',
        language: 'zh-CN',
        autoSave: true
    },
    
    // API配置
    api: {
        baseUrl: '/api/v1',
        timeout: 30000,
        retries: 3
    },
    
    // 缓存
    cache: {
        enabled: true,
        ttl: 300000 // 5分钟缓存
    },
    
    // 事件监听器
    events: {}
};

// 工具函数库
const Utils = {
    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 格式化时间
    formatTime(date) {
        if (!date) return '';
        
        const now = new Date();
        const targetDate = new Date(date);
        const diff = now - targetDate;
        
        const minute = 60 * 1000;
        const hour = minute * 60;
        const day = hour * 24;
        const week = day * 7;
        const month = day * 30;
        const year = day * 365;
        
        if (diff < minute) {
            return '刚刚';
        } else if (diff < hour) {
            return Math.floor(diff / minute) + '分钟前';
        } else if (diff < day) {
            return Math.floor(diff / hour) + '小时前';
        } else if (diff < week) {
            return Math.floor(diff / day) + '天前';
        } else if (diff < month) {
            return Math.floor(diff / week) + '周前';
        } else if (diff < year) {
            return Math.floor(diff / month) + '个月前';
        } else {
            return Math.floor(diff / year) + '年前';
        }
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 生成UUID
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },
    
    // 深拷贝对象
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (obj instanceof Object) {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },
    
    // 验证邮箱
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // 验证URL
    validateURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    // 获取查询参数
    getQueryParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    },
    
    // 设置查询参数
    setQueryParam(name, value) {
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set(name, value);
        window.history.replaceState({}, '', `${window.location.pathname}?${urlParams.toString()}`);
    },
    
    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // 降级处理
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                return true;
            } catch (err) {
                console.error('复制失败:', err);
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    },
    
    // 本地存储
    storage: {
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (err) {
                console.error('存储失败:', err);
                return false;
            }
        },
        
        get(key) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            } catch (err) {
                console.error('读取失败:', err);
                return null;
            }
        },
        
        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (err) {
                console.error('删除失败:', err);
                return false;
            }
        },
        
        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (err) {
                console.error('清空失败:', err);
                return false;
            }
        }
    }
};

// API服务
const ApiService = {
    // 基础请求方法
    async request(endpoint, options = {}) {
        const url = `${AppState.api.baseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };
        
        // 添加请求超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), AppState.api.timeout);
        
        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal,
                headers: {
                    ...config.headers,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('请求超时');
            }
            
            throw error;
        }
    },
    
    // GET请求
    async get(endpoint, params = {}) {
        const url = new URL(`${AppState.api.baseUrl}${endpoint}`, window.location.origin);
        
        // 添加查询参数
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search, { method: 'GET' });
    },
    
    // POST请求
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT请求
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
    
    // 上传文件
    async upload(endpoint, file, onProgress) {
        const formData = new FormData();
        formData.append('file', file);
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable && onProgress) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    onProgress(percentComplete);
                }
            };
            
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (err) {
                        reject(new Error('Invalid JSON response'));
                    }
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            };
            
            xhr.onerror = () => {
                reject(new Error('Network error'));
            };
            
            xhr.open('POST', `${AppState.api.baseUrl}${endpoint}`, true);
            xhr.send(formData);
        });
    }
};

// 事件系统
const EventSystem = {
    // 订阅事件
    on(event, callback) {
        if (!AppState.events[event]) {
            AppState.events[event] = [];
        }
        AppState.events[event].push(callback);
    },
    
    // 取消订阅
    off(event, callback) {
        if (!AppState.events[event]) return;
        
        const index = AppState.events[event].indexOf(callback);
        if (index > -1) {
            AppState.events[event].splice(index, 1);
        }
    },
    
    // 触发事件
    emit(event, data) {
        if (!AppState.events[event]) return;
        
        AppState.events[event].forEach(callback => {
            try {
                callback(data);
            } catch (err) {
                console.error(`Event handler error for ${event}:`, err);
            }
        });
    },
    
    // 一次性订阅
    once(event, callback) {
        const onceCallback = (data) => {
            callback(data);
            this.off(event, onceCallback);
        };
        this.on(event, onceCallback);
    }
};

// UI组件
const UI = {
    // 显示Toast通知
    showToast(title, message, type = 'info') {
        const toastEl = document.getElementById('toast');
        const toastTitle = document.getElementById('toast-title');
        const toastMessage = document.getElementById('toast-message');
        
        if (!toastEl) return;
        
        // 设置内容
        toastTitle.textContent = title;
        toastMessage.textContent = message;
        
        // 设置图标
        const icon = toastEl.querySelector('.toast-header i');
        if (icon) {
            icon.className = `fas me-2 ${this.getToastIcon(type)}`;
        }
        
        // 设置颜色
        const header = toastEl.querySelector('.toast-header');
        if (header) {
            header.className = `toast-header ${this.getToastClass(type)}`;
        }
        
        // 显示Toast
        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 5000
        });
        toast.show();
    },
    
    // 获取Toast图标
    getToastIcon(type) {
        const icons = {
            'success': 'fa-check-circle text-success',
            'error': 'fa-exclamation-circle text-danger',
            'warning': 'fa-exclamation-triangle text-warning',
            'info': 'fa-info-circle text-info'
        };
        return icons[type] || icons.info;
    },
    
    // 获取Toast样式
    getToastClass(type) {
        const classes = {
            'success': 'text-success',
            'error': 'text-danger',
            'warning': 'text-warning',
            'info': 'text-info'
        };
        return classes[type] || classes.info;
    },
    
    // 显示加载状态
    showLoading(element, text = '加载中...') {
        const originalContent = element.innerHTML;
        element.innerHTML = `
            <span class="loading-spinner me-2"></span>
            ${text}
        `;
        element.disabled = true;
        element.dataset.originalContent = originalContent;
    },
    
    // 隐藏加载状态
    hideLoading(element) {
        if (element.dataset.originalContent) {
            element.innerHTML = element.dataset.originalContent;
            element.disabled = false;
            delete element.dataset.originalContent;
        }
    },
    
    // 显示确认对话框
    confirm(message, title = '确认') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-danger" id="confirm-btn">确认</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            const confirmBtn = modal.querySelector('#confirm-btn');
            confirmBtn.addEventListener('click', () => {
                bsModal.hide();
                resolve(true);
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
                resolve(false);
            });
        });
    },
    
    // 显示输入对话框
    prompt(message, defaultValue = '', title = '输入') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                            <input type="text" class="form-control" id="prompt-input" value="${defaultValue}">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="prompt-btn">确认</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            const input = modal.querySelector('#prompt-input');
            const promptBtn = modal.querySelector('#prompt-btn');
            
            // 自动聚焦
            setTimeout(() => input.focus(), 100);
            
            // 回车确认
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    promptBtn.click();
                }
            });
            
            promptBtn.addEventListener('click', () => {
                bsModal.hide();
                resolve(input.value);
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
                resolve(null);
            });
        });
    },
    
    // 平滑滚动到元素
    scrollToElement(element, offset = 0) {
        const targetElement = typeof element === 'string' ? 
            document.querySelector(element) : element;
        
        if (targetElement) {
            const targetPosition = targetElement.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    },
    
    // 高亮元素
    highlightElement(element, duration = 2000) {
        const targetElement = typeof element === 'string' ? 
            document.querySelector(element) : element;
        
        if (targetElement) {
            targetElement.style.transition = 'background-color 0.3s ease';
            targetElement.style.backgroundColor = '#fff3cd';
            
            setTimeout(() => {
                targetElement.style.backgroundColor = '';
            }, duration);
        }
    }
};

// 表单验证
const FormValidator = {
    // 验证规则
    rules: {
        required: (value) => value !== null && value !== undefined && value.toString().trim() !== '',
        email: (value) => Utils.validateEmail(value),
        url: (value) => Utils.validateURL(value),
        minLength: (value, min) => value.length >= min,
        maxLength: (value, max) => value.length <= max,
        pattern: (value, pattern) => new RegExp(pattern).test(value),
        numeric: (value) => !isNaN(value) && isFinite(value),
        integer: (value) => Number.isInteger(Number(value)),
        positive: (value) => Number(value) > 0,
        range: (value, min, max) => value >= min && value <= max
    },
    
    // 验证表单
    validate(form, rules) {
        const errors = {};
        const formData = new FormData(form);
        
        for (const [fieldName, fieldRules] of Object.entries(rules)) {
            const value = formData.get(fieldName) || form.elements[fieldName]?.value;
            
            for (const rule of fieldRules) {
                const [ruleName, ...params] = rule.split(':');
                const validator = this.rules[ruleName];
                
                if (validator && !validator(value, ...params)) {
                    if (!errors[fieldName]) {
                        errors[fieldName] = [];
                    }
                    errors[fieldName].push(this.getErrorMessage(ruleName, ...params));
                }
            }
        }
        
        return errors;
    },
    
    // 获取错误消息
    getErrorMessage(ruleName, ...params) {
        const messages = {
            required: '此字段为必填项',
            email: '请输入有效的邮箱地址',
            url: '请输入有效的URL',
            minLength: `最少需要${params[0]}个字符`,
            maxLength: `最多允许${params[0]}个字符`,
            pattern: '格式不正确',
            numeric: '请输入数字',
            integer: '请输入整数',
            positive: '请输入正数',
            range: `值应在${params[0]}到${params[1]}之间`
        };
        
        return messages[ruleName] || '验证失败';
    },
    
    // 显示错误信息
    showErrors(form, errors) {
        // 清除现有错误
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
        
        // 显示新错误
        for (const [fieldName, fieldErrors] of Object.entries(errors)) {
            const field = form.elements[fieldName];
            if (field) {
                field.classList.add('is-invalid');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = fieldErrors[0];
                field.parentNode.appendChild(errorDiv);
            }
        }
    },
    
    // 清除错误
    clearErrors(form) {
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
    }
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化应用
    initializeApp();
    
    // 绑定全局事件
    bindGlobalEvents();
    
    // 加载用户设置
    loadUserSettings();
    
    // 触发页面加载完成事件
    EventSystem.emit('app:ready');
});

// 初始化应用
function initializeApp() {
    // 检测浏览器兼容性
    checkBrowserCompatibility();
    
    // 初始化主题
    initializeTheme();
    
    // 初始化语言
    initializeLanguage();
    
    // 绑定表单验证
    bindFormValidation();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化返回顶部按钮
    initializeBackToTop();
}

// 绑定全局事件
function bindGlobalEvents() {
    // 处理AJAX错误
    window.addEventListener('unhandledrejection', function(event) {
        if (event.reason instanceof Error) {
            console.error('Unhandled promise rejection:', event.reason);
            UI.showToast('错误', event.reason.message, 'error');
        }
    });
    
    // 处理网络状态变化
    window.addEventListener('online', function() {
        UI.showToast('网络已恢复', '网络连接已恢复', 'success');
    });
    
    window.addEventListener('offline', function() {
        UI.showToast('网络已断开', '网络连接已断开', 'warning');
    });
    
    // 处理页面卸载
    window.addEventListener('beforeunload', function(event) {
        // 如果有未保存的更改，提示用户
        if (hasUnsavedChanges()) {
            event.preventDefault();
            event.returnValue = '';
        }
    });
}

// 检查浏览器兼容性
function checkBrowserCompatibility() {
    const requiredFeatures = [
        'fetch',
        'Promise',
        'localStorage',
        'sessionStorage',
        'URLSearchParams'
    ];
    
    const missingFeatures = requiredFeatures.filter(feature => !(feature in window));
    
    if (missingFeatures.length > 0) {
        console.warn('浏览器缺少以下特性:', missingFeatures);
        UI.showToast('浏览器兼容性警告', 
            `您的浏览器可能缺少一些必要特性，建议使用现代浏览器`, 'warning');
    }
}

// 初始化主题
function initializeTheme() {
    const savedTheme = Utils.storage.get('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// 初始化语言
function initializeLanguage() {
    const savedLanguage = Utils.storage.get('language') || 'zh-CN';
    document.documentElement.setAttribute('lang', savedLanguage);
}

// 绑定表单验证
function bindFormValidation() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(event) {
            const rules = JSON.parse(form.dataset.validate || '{}');
            const errors = FormValidator.validate(form, rules);
            
            if (Object.keys(errors).length > 0) {
                event.preventDefault();
                FormValidator.showErrors(form, errors);
                UI.showToast('表单验证失败', '请检查输入内容', 'error');
            } else {
                FormValidator.clearErrors(form);
            }
        });
    });
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化返回顶部按钮
function initializeBackToTop() {
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'btn btn-primary position-fixed bottom-0 end-0 m-3';
    backToTopBtn.style.display = 'none';
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.setAttribute('title', '返回顶部');
    
    document.body.appendChild(backToTopBtn);
    
    // 监听滚动事件
    window.addEventListener('scroll', Utils.throttle(function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    }, 100));
    
    // 点击返回顶部
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 加载用户设置
function loadUserSettings() {
    const savedSettings = Utils.storage.get('userSettings');
    if (savedSettings) {
        Object.assign(AppState.settings, savedSettings);
    }
}

// 保存用户设置
function saveUserSettings() {
    Utils.storage.set('userSettings', AppState.settings);
}

// 检查是否有未保存的更改
function hasUnsavedChanges() {
    // 这里可以根据实际情况检查是否有未保存的更改
    return false;
}

// 导出全局对象
window.App = {
    State: AppState,
    Utils: Utils,
    API: ApiService,
    Events: EventSystem,
    UI: UI,
    Validator: FormValidator
};