package service

import (
	"errors"
	"time"

	"github.com/cfrs2005/ppmtest/internal/models"
	"github.com/cfrs2005/ppmtest/internal/repository"
)

var (
	ErrPostTitleRequired   = errors.New("post title is required")
	ErrPostContentRequired = errors.New("post content is required")
	ErrInvalidStatus       = errors.New("invalid post status")
)

// PostService defines the interface for post business logic
type PostService interface {
	CreatePost(post *models.Post, authorID uint) error
	GetPostByID(id uint) (*models.Post, error)
	GetPostBySlug(slug string) (*models.Post, error)
	UpdatePost(post *models.Post, authorID uint) error
	DeletePost(id uint, authorID uint) error
	ListPosts(page, pageSize int, status string) ([]*models.Post, int64, error)
	GetUserPosts(authorID uint, page, pageSize int) ([]*models.Post, int64, error)
	SearchPosts(query string, page, pageSize int) ([]*models.Post, int64, error)
	PublishPost(id uint, authorID uint) error
	IncrementViewCount(id uint) error
}

type postService struct {
	postRepo repository.PostRepository
	userRepo repository.UserRepository
}

// NewPostService creates a new post service
func NewPostService(postRepo repository.PostRepository, userRepo repository.UserRepository) PostService {
	return &postService{
		postRepo: postRepo,
		userRepo: userRepo,
	}
}

func (s *postService) CreatePost(post *models.Post, authorID uint) error {
	if post.Title == "" {
		return ErrPostTitleRequired
	}

	if post.Content == "" {
		return ErrPostContentRequired
	}

	author, err := s.userRepo.FindByID(authorID)
	if err != nil {
		return err
	}

	if author.Status != "active" {
		return ErrUserInactive
	}

	if post.Slug == "" {
		post.Slug = generateSlug(post.Title)
	}

	if post.Status == "" {
		post.Status = "draft"
	}

	post.AuthorID = authorID

	return s.postRepo.Create(post)
}

func (s *postService) GetPostByID(id uint) (*models.Post, error) {
	post, err := s.postRepo.FindByID(id)
	if err != nil {
		return nil, err
	}

	if err := s.IncrementViewCount(id); err != nil {
		return post, err
	}

	return post, nil
}

func (s *postService) GetPostBySlug(slug string) (*models.Post, error) {
	post, err := s.postRepo.FindBySlug(slug)
	if err != nil {
		return nil, err
	}

	if err := s.IncrementViewCount(post.ID); err != nil {
		return post, err
	}

	return post, nil
}

func (s *postService) UpdatePost(post *models.Post, authorID uint) error {
	existingPost, err := s.postRepo.FindByID(post.ID)
	if err != nil {
		return err
	}

	if existingPost.AuthorID != authorID {
		return ErrUnauthorized
	}

	if post.Title == "" {
		return ErrPostTitleRequired
	}

	if post.Slug == "" {
		post.Slug = generateSlug(post.Title)
	}

	post.AuthorID = authorID
	return s.postRepo.Update(post)
}

func (s *postService) DeletePost(id uint, authorID uint) error {
	post, err := s.postRepo.FindByID(id)
	if err != nil {
		return err
	}

	if post.AuthorID != authorID {
		return ErrUnauthorized
	}

	return s.postRepo.Delete(id)
}

func (s *postService) ListPosts(page, pageSize int, status string) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.List(offset, pageSize, status)
}

func (s *postService) GetUserPosts(authorID uint, page, pageSize int) ([]*models.Post, int64, error) {
	offset := (page - 1) * pageSize
	return s.postRepo.FindByAuthor(authorID, offset, pageSize)
}

func (s *postService) SearchPosts(query string, page, pageSize int) ([]*models.Post, int64, error) {
	if query == "" {
		return []*models.Post{}, 0, nil
	}

	offset := (page - 1) * pageSize
	return s.postRepo.Search(query, offset, pageSize)
}

func (s *postService) PublishPost(id uint, authorID uint) error {
	post, err := s.postRepo.FindByID(id)
	if err != nil {
		return err
	}

	if post.AuthorID != authorID {
		return ErrUnauthorized
	}

	post.Status = "published"
	now := time.Now()
	post.PublishedAt = &now

	return s.postRepo.Update(post)
}

func (s *postService) IncrementViewCount(id uint) error {
	post, err := s.postRepo.FindByID(id)
	if err != nil {
		return err
	}

	post.ViewCount++
	return s.postRepo.Update(post)
}

func generateSlug(title string) string {
	return title
}