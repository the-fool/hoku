var postcss = require('gulp-postcss');
var gulp = require('gulp');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var htmlmin = require('gulp-htmlmin');
var babel = require('gulp-babel');
var sass = require('gulp-sass');
require('gulp-watch');
require('babel-preset-es2015');


gulp.task('sass', function() {
  var plugins = [
    autoprefixer({
      browsers: ['last 5 versions']
    }),
    cssnano()
  ];
  return gulp.src('./**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('js', function() {
  gulp.src(['./*.js', '!gulpfile.js'])
    .pipe(babel({
      presets: ['es2015']
    }))
    .pipe(gulp.dest('./public'));
});

gulp.task('css', function() {
  var plugins = [
    autoprefixer({
      browsers: ['last 5 versions']
    }),
    cssnano()
  ];
  return gulp.src('./*.css')
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('watch', function () {
  gulp.watch(['./*.js', './*.scss', '!./gulpfile.js'], ['build']);
});

gulp.task('build', ['sass', 'js']);
