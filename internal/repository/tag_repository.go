package repository

import (
	"errors"

	"github.com/cfrs2005/ppmtest/internal/models"
	"gorm.io/gorm"
)

var (
	ErrTagNotFound = errors.New("tag not found")
)

// TagRepository defines the interface for tag data operations
type TagRepository interface {
	Create(tag *models.Tag) error
	FindByID(id uint) (*models.Tag, error)
	FindBySlug(slug string) (*models.Tag, error)
	Update(tag *models.Tag) error
	Delete(id uint) error
	List(offset, limit int) ([]*models.Tag, int64, error)
}

type tagRepository struct {
	db *gorm.DB
}

// NewTagRepository creates a new tag repository
func NewTagRepository(db *gorm.DB) TagRepository {
	return &tagRepository{db: db}
}

func (r *tagRepository) Create(tag *models.Tag) error {
	result := r.db.Create(tag)
	return result.Error
}

func (r *tagRepository) FindByID(id uint) (*models.Tag, error) {
	var tag models.Tag
	result := r.db.First(&tag, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrTagNotFound
		}
		return nil, result.Error
	}
	return &tag, nil
}

func (r *tagRepository) FindBySlug(slug string) (*models.Tag, error) {
	var tag models.Tag
	result := r.db.Where("slug = ?", slug).First(&tag)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrTagNotFound
		}
		return nil, result.Error
	}
	return &tag, nil
}

func (r *tagRepository) Update(tag *models.Tag) error {
	result := r.db.Save(tag)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrTagNotFound
	}
	return nil
}

func (r *tagRepository) Delete(id uint) error {
	result := r.db.Delete(&models.Tag{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrTagNotFound
	}
	return nil
}

func (r *tagRepository) List(offset, limit int) ([]*models.Tag, int64, error) {
	var tags []*models.Tag
	var total int64

	if err := r.db.Model(&models.Tag{}).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := r.db.Order("name ASC").Offset(offset).Limit(limit).Find(&tags)
	if result.Error != nil {
		return nil, 0, result.Error
	}

	return tags, total, nil
}