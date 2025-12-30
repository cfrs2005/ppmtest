package handlers

import (
	"net/http"
	"strconv"

	"ppmtest/internal/models"

	"github.com/gin-gonic/gin"
)

type CommentHandler struct {
	commentService CommentService
}

type CommentService interface {
	Create(comment *models.Comment, authorID uint) error
	GetByID(id uint) (*models.Comment, error)
	Update(comment *models.Comment, userID uint) error
	Delete(id uint, userID uint) error
	GetByPostID(postID uint, page, pageSize int) ([]*models.Comment, int64, error)
	GetByAuthorID(authorID uint, page, pageSize int) ([]*models.Comment, int64, error)
	GetByStatus(status string, page, pageSize int) ([]*models.Comment, int64, error)
	Approve(id uint) error
	Reject(id uint) error
	MarkAsSpam(id uint) error
}

func NewCommentHandler(commentService CommentService) *CommentHandler {
	return &CommentHandler{
		commentService: commentService,
	}
}

type CreateCommentRequest struct {
	PostID  uint   `json:"post_id" binding:"required"`
	Content string `json:"content" binding:"required,min=1"`
}

type UpdateCommentRequest struct {
	Content string `json:"content" binding:"required,min=1"`
}

func (h *CommentHandler) Create(c *gin.Context) {
	authorID := c.GetUint("user_id")

	var req CreateCommentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	comment := &models.Comment{
		PostID:  req.PostID,
		Content: req.Content,
	}

	if err := h.commentService.Create(comment, authorID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Comment created successfully",
		"comment": comment,
	})
}

func (h *CommentHandler) GetByID(c *gin.Context) {
	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	comment, err := h.commentService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Comment not found"})
		return
	}

	c.JSON(http.StatusOK, comment)
}

func (h *CommentHandler) Update(c *gin.Context) {
	userID := c.GetUint("user_id")

	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	var req UpdateCommentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	comment, err := h.commentService.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Comment not found"})
		return
	}

	comment.Content = req.Content

	if err := h.commentService.Update(comment, userID); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Comment updated successfully",
		"comment": comment,
	})
}

func (h *CommentHandler) Delete(c *gin.Context) {
	userID := c.GetUint("user_id")

	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	if err := h.commentService.Delete(uint(id), userID); err != nil {
		c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Comment deleted successfully"})
}

func (h *CommentHandler) GetByPostID(c *gin.Context) {
	postIDParam := c.Param("post_id")
	postID, err := strconv.ParseUint(postIDParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid post ID"})
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

	comments, total, err := h.commentService.GetByPostID(uint(postID), page, pageSize)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"comments": comments,
		"pagination": gin.H{
			"page":        page,
			"page_size":   pageSize,
			"total":       total,
			"total_pages": (total + int64(pageSize) - 1) / int64(pageSize),
		},
	})
}

func (h *CommentHandler) Approve(c *gin.Context) {
	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	if err := h.commentService.Approve(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Comment approved successfully"})
}

func (h *CommentHandler) Reject(c *gin.Context) {
	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	if err := h.commentService.Reject(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Comment rejected successfully"})
}

func (h *CommentHandler) MarkAsSpam(c *gin.Context) {
	idParam := c.Param("id")
	id, err := strconv.ParseUint(idParam, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid comment ID"})
		return
	}

	if err := h.commentService.MarkAsSpam(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Comment marked as spam"})
}
