package repository

import (
	"errors"

	"ppmtest/internal/models"

	"gorm.io/gorm"
)

var (
	ErrCategoryNotFound      = errors.New("category not found")
	ErrCategoryAlreadyExists = errors.New("category already exists")
)

type CategoryRepository interface {
	Create(category *models.Category) error
	GetByID(id uint) (*models.Category, error)
	GetBySlug(slug string) (*models.Category, error)
	Update(category *models.Category) error
	Delete(id uint) error
	List(offset, limit int) ([]*models.Category, int64, error)
	GetByName(name string) (*models.Category, error)
}

type categoryRepository struct {
	db *gorm.DB
}

func NewCategoryRepository(db *gorm.DB) CategoryRepository {
	return &categoryRepository{db: db}
}

func (r *categoryRepository) Create(category *models.Category) error {
	result := r.db.Create(category)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrDuplicatedKey) {
			return ErrCategoryAlreadyExists
		}
		return result.Error
	}
	return nil
}

func (r *categoryRepository) GetByID(id uint) (*models.Category, error) {
	var category models.Category
	result := r.db.First(&category, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrCategoryNotFound
		}
		return nil, result.Error
	}
	return &category, nil
}

func (r *categoryRepository) GetBySlug(slug string) (*models.Category, error) {
	var category models.Category
	result := r.db.Where("slug = ?", slug).First(&category)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrCategoryNotFound
		}
		return nil, result.Error
	}
	return &category, nil
}

func (r *categoryRepository) Update(category *models.Category) error {
	result := r.db.Save(category)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrCategoryNotFound
	}
	return nil
}

func (r *categoryRepository) Delete(id uint) error {
	result := r.db.Delete(&models.Category{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrCategoryNotFound
	}
	return nil
}

func (r *categoryRepository) List(offset, limit int) ([]*models.Category, int64, error) {
	var categories []*models.Category
	var total int64

	if err := r.db.Model(&models.Category{}).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := r.db.Order("name ASC").Offset(offset).Limit(limit).Find(&categories)
	if result.Error != nil {
		return nil, 0, result.Error
	}

	return categories, total, nil
}

func (r *categoryRepository) GetByName(name string) (*models.Category, error) {
	var category models.Category
	result := r.db.Where("name = ?", name).First(&category)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrCategoryNotFound
		}
		return nil, result.Error
	}
	return &category, nil
}
