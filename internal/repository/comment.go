package repository

import (
	"errors"

	"ppmtest/internal/models"

	"gorm.io/gorm"
)

var (
	ErrCommentNotFound = errors.New("comment not found")
)

type CommentRepository interface {
	Create(comment *models.Comment) error
	GetByID(id uint) (*models.Comment, error)
	Update(comment *models.Comment) error
	Delete(id uint) error
	GetByPostID(postID uint, offset, limit int) ([]*models.Comment, int64, error)
	GetByAuthorID(authorID uint, offset, limit int) ([]*models.Comment, int64, error)
	GetByStatus(status string, offset, limit int) ([]*models.Comment, int64, error)
}

type commentRepository struct {
	db *gorm.DB
}

func NewCommentRepository(db *gorm.DB) CommentRepository {
	return &commentRepository{db: db}
}

func (r *commentRepository) Create(comment *models.Comment) error {
	result := r.db.Create(comment)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func (r *commentRepository) GetByID(id uint) (*models.Comment, error) {
	var comment models.Comment
	result := r.db.Preload("Post").Preload("Author").First(&comment, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrCommentNotFound
		}
		return nil, result.Error
	}
	return &comment, nil
}

func (r *commentRepository) Update(comment *models.Comment) error {
	result := r.db.Save(comment)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrCommentNotFound
	}
	return nil
}

func (r *commentRepository) Delete(id uint) error {
	result := r.db.Delete(&models.Comment{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrCommentNotFound
	}
	return nil
}

func (r *commentRepository) GetByPostID(postID uint, offset, limit int) ([]*models.Comment, int64, error) {
	var comments []*models.Comment
	var total int64

	query := r.db.Model(&models.Comment{}).Where("post_id = ?", postID)

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := query.Preload("Author").Order("created_at DESC").Offset(offset).Limit(limit).Find(&comments)
	if result.Error != nil {
		return nil, 0, result.Error
	}

	return comments, total, nil
}

func (r *commentRepository) GetByAuthorID(authorID uint, offset, limit int) ([]*models.Comment, int64, error) {
	var comments []*models.Comment
	var total int64

	query := r.db.Model(&models.Comment{}).Where("author_id = ?", authorID)

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := query.Preload("Post").Preload("Author").Order("created_at DESC").Offset(offset).Limit(limit).Find(&comments)
	if result.Error != nil {
		return nil, 0, result.Error
	}

	return comments, total, nil
}

func (r *commentRepository) GetByStatus(status string, offset, limit int) ([]*models.Comment, int64, error) {
	var comments []*models.Comment
	var total int64

	query := r.db.Model(&models.Comment{}).Where("status = ?", status)

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	result := query.Preload("Post").Preload("Author").Order("created_at DESC").Offset(offset).Limit(limit).Find(&comments)
	if result.Error != nil {
		return nil, 0, result.Error
	}

	return comments, total, nil
}
