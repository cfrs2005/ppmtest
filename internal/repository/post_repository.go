package repository

import (
	"errors"

	"github.com/cfrs2005/ppmtest/internal/models"
	"gorm.io/gorm"
)

var (
	ErrPostNotFound      = errors.New("post not found")
	ErrPostAlreadyExists = errors.New("post already exists")
)

// PostRepository defines the interface for post data operations
type PostRepository interface {
	Create(post *models.Post) error
	FindByID(id uint) (*models.Post, error)
	FindBySlug(slug string) (*models.Post, error)
	Update(post *models.Post) error
	Delete(id uint) error
	List(offset, limit int, status string) ([]*models.Post, int64, error)
	FindByAuthor(authorID uint, offset, limit int) ([]*models.Post, int64, error)
	Search(query string, offset, limit int) ([]*models.Post, int64, error)
}

type postRepository struct {
	db *gorm.DB
}

// NewPostRepository creates a new post repository
func NewPostRepository(db *gorm.DB) PostRepository {
	return &postRepository{db: db}
}

func (r *postRepository) Create(post *models.Post) error {
	result := r.db.Create(post)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrDuplicatedKey) {
			return ErrPostAlreadyExists
		}
		return result.Error
	}
	return nil
}

func (r *postRepository) FindByID(id uint) (*models.Post, error) {
	var post models.Post
	result := r.db.Preload("Author").First(&post, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrPostNotFound
		}
		return nil, result.Error
	}
	return &post, nil
}

func (r *postRepository) FindBySlug(slug string) (*models.Post, error) {
	var post models.Post
	result := r.db.Preload("Author").Where("slug = ?", slug).First(&post)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrPostNotFound
		}
		return nil, result.Error
	}
	return &post, nil
}

func (r *postRepository) Update(post *models.Post) error {
	result := r.db.Save(post)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrPostNotFound
	}
	return nil
}

func (r *postRepository) Delete(id uint) error {
	result := r.db.Delete(&models.Post{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrPostNotFound
	}
	return nil
}

func (r *postRepository) List(offset, limit int, status string) ([]*models.Post, int64, error) {
	var posts []*models.Post
	var total int64

	query := r.db.Model(&models.Post{})
	if status != "" && status != "all" {
		query = query.Where("status = ?", status)
	}

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := query.Preload("Author").
		Order("created_at DESC").
		Offset(offset).
		Limit(limit).
		Find(&posts)

	if result.Error != nil {
		return nil, 0, result.Error
	}

	return posts, total, nil
}

func (r *postRepository) FindByAuthor(authorID uint, offset, limit int) ([]*models.Post, int64, error) {
	var posts []*models.Post
	var total int64

	query := r.db.Model(&models.Post{}).Where("author_id = ?", authorID)

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := query.Order("created_at DESC").
		Offset(offset).
		Limit(limit).
		Find(&posts)

	if result.Error != nil {
		return nil, 0, result.Error
	}

	return posts, total, nil
}

func (r *postRepository) Search(query string, offset, limit int) ([]*models.Post, int64, error) {
	var posts []*models.Post
	var total int64

	searchQuery := r.db.Model(&models.Post{}).Where(
		"title LIKE ? OR content LIKE ? OR summary LIKE ?",
		"%"+query+"%", "%"+query+"%", "%"+query+"%",
	)

	if err := searchQuery.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := searchQuery.Preload("Author").
		Order("created_at DESC").
		Offset(offset).
		Limit(limit).
		Find(&posts)

	if result.Error != nil {
		return nil, 0, result.Error
	}

	return posts, total, nil
}