package service

import (
	"errors"
	"strings"
	"time"

	"ppmtest/internal/models"
	"ppmtest/internal/repository"
)

var (
	ErrUnauthorizedPost = errors.New("unauthorized to modify this post")
)

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

type postService struct {
	postRepo repository.PostRepository
}

func NewPostService(postRepo repository.PostRepository) PostService {
	return &postService{
		postRepo: postRepo,
	}
}

func (s *postService) Create(post *models.Post, authorID uint) error {
	post.AuthorID = authorID
	post.Status = "draft"

	if post.Slug == "" {
		post.Slug = generateSlug(post.Title)
	}

	return s.postRepo.Create(post)
}

func (s *postService) GetByID(id uint) (*models.Post, error) {
	return s.postRepo.GetByID(id)
}

func (s *postService) GetBySlug(slug string) (*models.Post, error) {
	return s.postRepo.GetBySlug(slug)
}

func (s *postService) Update(post *models.Post, userID uint) error {
	existingPost, err := s.postRepo.GetByID(post.ID)
	if err != nil {
		return err
	}

	if existingPost.AuthorID != userID {
		return ErrUnauthorizedPost
	}

	if post.Slug == "" {
		post.Slug = generateSlug(post.Title)
	}

	return s.postRepo.Update(post)
}

func (s *postService) Delete(id uint, userID uint) error {
	post, err := s.postRepo.GetByID(id)
	if err != nil {
		return err
	}

	if post.AuthorID != userID {
		return ErrUnauthorizedPost
	}

	return s.postRepo.Delete(id)
}

func (s *postService) List(page, pageSize int) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.List(offset, pageSize)
}

func (s *postService) GetByAuthorID(authorID uint, page, pageSize int) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.GetByAuthorID(authorID, offset, pageSize)
}

func (s *postService) GetByStatus(status string, page, pageSize int) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.GetByStatus(status, offset, pageSize)
}

func (s *postService) Search(query string, page, pageSize int) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.Search(query, offset, pageSize)
}

func (s *postService) Publish(id uint, userID uint) error {
	post, err := s.postRepo.GetByID(id)
	if err != nil {
		return err
	}

	if post.AuthorID != userID {
		return ErrUnauthorizedPost
	}

	post.Status = "published"
	now := time.Now()
	post.PublishedAt = &now

	return s.postRepo.Update(post)
}

func generateSlug(title string) string {
	slug := strings.ToLower(title)
	slug = strings.ReplaceAll(slug, " ", "-")
	slug = strings.ReplaceAll(slug, "?", "")
	slug = strings.ReplaceAll(slug, "!", "")
	slug = strings.ReplaceAll(slug, ".", "")
	
	if len(slug) > 100 {
		slug = slug[:100]
	}

	return slug
}
