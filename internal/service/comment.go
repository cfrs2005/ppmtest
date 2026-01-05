package service

import (
	"errors"

	"ppmtest/internal/models"
	"ppmtest/internal/repository"
)

var (
	ErrUnauthorizedComment = errors.New("unauthorized to modify this comment")
)

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

type commentService struct {
	commentRepo repository.CommentRepository
}

func NewCommentService(commentRepo repository.CommentRepository) CommentService {
	return &commentService{
		commentRepo: commentRepo,
	}
}

func (s *commentService) Create(comment *models.Comment, authorID uint) error {
	comment.AuthorID = authorID
	comment.Status = "pending"

	return s.commentRepo.Create(comment)
}

func (s *commentService) GetByID(id uint) (*models.Comment, error) {
	return s.commentRepo.GetByID(id)
}

func (s *commentService) Update(comment *models.Comment, userID uint) error {
	existingComment, err := s.commentRepo.GetByID(comment.ID)
	if err != nil {
		return err
	}

	if existingComment.AuthorID != userID {
		return ErrUnauthorizedComment
	}

	return s.commentRepo.Update(comment)
}

func (s *commentService) Delete(id uint, userID uint) error {
	comment, err := s.commentRepo.GetByID(id)
	if err != nil {
		return err
	}

	if comment.AuthorID != userID {
		return ErrUnauthorizedComment
	}

	return s.commentRepo.Delete(id)
}

func (s *commentService) GetByPostID(postID uint, page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	return s.commentRepo.GetByPostID(postID, offset, pageSize)
}

func (s *commentService) GetByAuthorID(authorID uint, page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	return s.commentRepo.GetByAuthorID(authorID, offset, pageSize)
}

func (s *commentService) GetByStatus(status string, page, pageSize int) ([]*models.Comment, int64, error) {
	offset := (page - 1) * pageSize
	return s.commentRepo.GetByStatus(status, offset, pageSize)
}

func (s *commentService) Approve(id uint) error {
	comment, err := s.commentRepo.GetByID(id)
	if err != nil {
		return err
	}

	comment.Status = "approved"
	return s.commentRepo.Update(comment)
}

func (s *commentService) Reject(id uint) error {
	comment, err := s.commentRepo.GetByID(id)
	if err != nil {
		return err
	}

	comment.Status = "pending"
	return s.commentRepo.Update(comment)
}

func (s *commentService) MarkAsSpam(id uint) error {
	comment, err := s.commentRepo.GetByID(id)
	if err != nil {
		return err
	}

	comment.Status = "spam"
	return s.commentRepo.Update(comment)
}
