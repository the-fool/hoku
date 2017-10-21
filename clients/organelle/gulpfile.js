var postcss = require('gulp-postcss');
var gulp = require('gulp');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var htmlmin = require('gulp-htmlmin');
const gulp = require('gulp');
const babel = require('gulp-babel');

gulp.task('js', () =>
          gulp.src('./*.js')
          .pipe(babel({
            presets: ['env']
          }))
          .pipe(gulp.dest('./public'))
         );

gulp.task('css', function () {
  var plugins = [
    autoprefixer({browsers: ['last 1 version']}),
    cssnano()
  ];
  return gulp.src('./*.css')
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('build', ['css']);
