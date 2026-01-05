package handlers

import (
	"net/http"
	"strconv"

	"ppmtest/internal/models"

	"github.com/gin-gonic/gin"
)

type PostHandler struct {
	postService PostService
}

type PostService interface {
	Create(post *models.Post, authorID uint) error
	GetByID(id uint) (*models.Post, error)
	GetBySlug(slug string) (*models.Post, error)
	Update(post *models.Post, userID uint) error
	Delete(id uint, userID uint) error
	List(page, pageSize int) ([]*models.Post, int64, error)
	GetByAuthorID(authorID uint, page, pageSize int) ([]*models.Post, int64, error)
	GetByStatus(status string, page, pageSize int) ([]*models.Post, int64, error)
	Search(query string, page, pageSize int) ([]*models.Post, int64, error)
	Publish(id uint, userID uint) error
}

func NewPostHandler(postService PostService) *PostHandler {
	return &PostHandler{
		postService: postService,
	}
}

type CreatePostRequest struct {
	Title   string `json:"title" binding:"required,min=1,max=255"`
	Slug    string `json:"slug" binding:"omitempty,max=255"`
	Content string `json:"content" binding:"required"`
	Summary string `json:"summary" binding:"omitempty"`
}

type UpdatePostRequest struct {
	Title   string `json:"title" binding:"omitempty,min=1,max=255"`
	Slug    string `json:"slug" binding:"omitempty,max=255"`
	Content string `json:"content" binding:"omitempty"`
	Summary string `json:"summary" binding:"omitempty"`
	Status  string `json:"status" binding:"omitempty,oneof=draft published archived"`
}

func (h *PostHandler) Create(c *gin.Context) {
	authorID := c.GetUint("user_id")

	var req CreatePostRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	post := &models.Post{
		Title:   req.Title,
		Slug:    req.Slug,
		Content: req.Content,
		Summary: req.Summary,
	}

	if err := h.postService.Create(post, authorID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Post created successfully",
		"post":    post,
	})
}

func (h *PostHandler) GetByID(c *gin.Context) {
	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid post ID"})
		return
	}

	post, err := h.postService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func (h *PostHandler) GetBySlug(c *gin.Context) {
	slug := c.Param("slug")

	post, err := h.postService.GetBySlug(slug)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func (h *PostHandler) Update(c *gin.Context) {
	userID := c.GetUint("user_id")

	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid post ID"})
		return
	}

	var req UpdatePostRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	post, err := h.postService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	if req.Title != "" {
		post.Title = req.Title
	}
	if req.Slug != "" {
		post.Slug = req.Slug
	}
	if req.Content != "" {
		post.Content = req.Content
	}
	if req.Summary != "" {
		post.Summary = req.Summary
	}
	if req.Status != "" {
		post.Status = req.Status
	}

	if err := h.postService.Update(post, userID); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Post updated successfully",
		"post":    post,
	})
}

func (h *PostHandler) Delete(c *gin.Context) {
	userID := c.GetUint("user_id")

	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid post ID"})
		return
	}

	if err := h.postService.Delete(uint(id), userID); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Post deleted successfully"})
}

func (h *PostHandler) List(c *gin.Context) {
	pageParam := c.DefaultQuery("page", "1")
	pageSizeParam := c.DefaultQuery("page_size", "10")

	page, err := strconv.Atoi(pageParam)
	if err != nil || page < 1 {
		page = 1
	}

	pageSize, err := strconv.Atoi(pageSizeParam)
	if err != nil || pageSize < 1 || pageSize > 100 {
		pageSize = 10
	}

	posts, total, err := h.postService.List(page, pageSize)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"posts": posts,
		"pagination": gin.H{
			"page":        page,
			"page_size":   pageSize,
			"total":       total,
			"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		},
	})
}

func (h *PostHandler) Search(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Query parameter 'q' is required"})
		return
	}

	pageParam := c.DefaultQuery("page", "1")
	pageSizeParam := c.DefaultQuery("page_size", "10")

	page, err := strconv.Atoi(pageParam)
	if err != nil || page < 1 {
		page = 1
	}

	pageSize, err := strconv.Atoi(pageSizeParam)
	if err != nil || pageSize < 1 || pageSize > 100 {
		pageSize = 10
	}

	posts, total, err := h.postService.Search(query, page, pageSize)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"posts": posts,
		"pagination": gin.H{
			"page":        page,
			"page_size":   pageSize,
			"total":       total,
			"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		},
		"query": query,
	})
}

func (h *PostHandler) Publish(c *gin.Context) {
	userID := c.GetUint("user_id")

	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid post ID"})
		return
	}

	if err := h.postService.Publish(uint(id), userID); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Post published successfully"})
}
