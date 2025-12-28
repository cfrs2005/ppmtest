package service

import (
	"errors"

	"github.com/cfrs2005/ppmtest/internal/models"
	"github.com/cfrs2005/ppmtest/internal/repository"
)

var (
	ErrCommentContentRequired = errors.New("comment content is required")
	ErrPostNotFound           = errors.New("post not found")
)

// CommentService defines the interface for comment business logic
type CommentService interface {
	CreateComment(comment *models.Comment, authorID uint) error
	GetComment(id uint) (*models.Comment, error)
	UpdateComment(comment *models.Comment, authorID uint) error
	DeleteComment(id uint, authorID uint) error
	GetPostComments(postID uint, page, pageSize int) ([]*models.Comment, int64, error)
	GetUserComments(authorID uint, page, pageSize int) ([]*models.Comment, int64, error)
	GetPendingComments(page, pageSize int) ([]*models.Comment, int64, error)
	ApproveComment(id uint) error
	RejectComment(id uint) error
}

type commentService struct {
	commentRepo repository.CommentRepository
	postRepo    repository.PostRepository
	userRepo    repository.UserRepository
}

// NewCommentService creates a new comment service
func NewCommentService(
	commentRepo repository.CommentRepository,
	postRepo repository.PostRepository,
	userRepo repository.UserRepository,
) CommentService {
	return &commentService{
		commentRepo: commentRepo,
		postRepo:    postRepo,
		userRepo:    userRepo,
	}
}

func (s *commentService) CreateComment(comment *models.Comment, authorID uint) error {
	if comment.Content == "" {
		return ErrCommentContentRequired
	}

	_, err := s.postRepo.FindByID(comment.PostID)
	if err != nil {
		if errors.Is(err, repository.ErrPostNotFound) {
			return ErrPostNotFound
		}
		return err
	}

	author, err := s.userRepo.FindByID(authorID)
	if err != nil {
		return err
	}

	if author.Status != "active" {
		return ErrUserInactive
	}

	comment.AuthorID = authorID
	comment.Status = "pending"

	return s.commentRepo.Create(comment)
}

func (s *commentService) GetComment(id uint) (*models.Comment, error) {
	return s.commentRepo.FindByID(id)
}

func (s *commentService) UpdateComment(comment *models.Comment, authorID uint) error {
	existingComment, err := s.commentRepo.FindByID(comment.ID)
	if err != nil {
		return err
	}

	if existingComment.AuthorID != authorID {
		return ErrUnauthorized
	}

	return s.commentRepo.Update(comment)
}

func (s *commentService) DeleteComment(id uint, authorID uint) error {
	comment, err := s.commentRepo.FindByID(id)
	if err != nil {
		return err
	}

	if comment.AuthorID != authorID {
		return ErrUnauthorized
	}

	return s.commentRepo.Delete(id)
}

func (s *commentService) GetPostComments(postID uint, page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	comments, total, err := s.commentRepo.FindByPost(postID, offset, pageSize)

	approvedComments := make([]*models.Comment, 0)
	for _, comment := range comments {
		if comment.Status == "approved" {
			approvedComments = append(approvedComments, comment)
		}
	}

	return approvedComments, total, err
}

func (s *commentService) GetUserComments(authorID uint, page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	return s.commentRepo.FindByAuthor(authorID, offset, pageSize)
}

func (s *commentService) GetPendingComments(page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	return s.commentRepo.ListPending(offset, pageSize)
}

func (s *commentService) ApproveComment(id uint) error {
	comment, err := s.commentRepo.FindByID(id)
	if err != nil {
		return err
	}

	comment.Status = "approved"
	return s.commentRepo.Update(comment)
}

func (s *commentService) RejectComment(id uint) error {
	comment, err := s.commentRepo.FindByID(id)
	if err != nil {
		return err
	}

	comment.Status = "spam"
	return s.commentRepo.Update(comment)
}