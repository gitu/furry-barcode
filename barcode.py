import os
import sys
import cStringIO
from flask import Flask, make_response, request, render_template, redirect, url_for, flash, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.graphics.barcode import getCodeNames, createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from datetime import datetime


app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route('/<code>')
def coded(code):
    value = request.args.get('value', '')
    count = request.args.get('count', '')
    scale = request.args.get('scale', '5')
    return render_template('main.html', code=code, value=value, count=count, scale=scale)


def genBarcode(code, value, canvas, scale):
    dr = createBarcodeDrawing(code, value=value, humanReadable=True)
    dr.renderScale = scale
    bounds = dr.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    dr.drawOn(canvas, (297*mm)/2-width*scale/2, (210*mm)/2-height*scale/2)
    canvas.drawString(1*mm, 1*mm, "generated at "+str(datetime.now()) + " from "+request.url)
    canvas.showPage()

@app.route('/', methods=[ 'GET'])
def form():
    code = request.args.get('code', '-')
    value = request.args.get('value', '-')
    count = request.args.get('count', '-')
    scale = request.args.get('scale', '5')
    action = request.args.get('action', '')
    if len(value) == 0:
        value = '0'
    if len(scale) == 0 or not scale.isdigit():
        scale = 5

    if code == '-':
        return render_template('main.html', codes=getCodeNames())

    try:
        if not (code in getCodeNames()):
            flash("Code "+code+" not supported allowed are : " + str(getCodeNames()))
            return render_template('main.html', codes=getCodeNames(), count=count, value=value, scale=scale)

        if value.isdigit() and count.isdigit():
            if int(count) > 1000:
                flash("Please enter a lower count - maximum is 1000.")
                return render_template('main.html', codes=getCodeNames(), code=code, count=count, value=value, scale=scale)

        if action == 'Generate PDF':
            if value.isdigit() and count.isdigit():
                return redirect(url_for('pdflist', code=code, scale=int(scale), start=value, count=count))
            else:
                return redirect(url_for('pdf', code=code, scale=int(scale), value=value))
        else:
            return render_template('main.html', codes=getCodeNames(), code=code, count=count, value=value,
                                   bcimage=url_for('img', code=code, scale=int(scale), value=value))


    except:
        flash("Error while generating a " + code + ": " + str(sys.exc_info()[0]))
        return render_template('main.html', code=code, codes=getCodeNames(), count=count, value=value)


@app.route('/<code>/<int:scale>/<int:start>/<int:count>')
def pdflist(code, start, count, scale):
    output = cStringIO.StringIO()

    p = canvas.Canvas(output, pagesize=landscape(A4))

    try:
        for i in range(count+0):
            genBarcode(code, str(start+i), p, scale)
    except:
        flash("Error while generating a " + code + ": " + str(sys.exc_info()[0]))
        return render_template('main.html', code=code, codes=getCodeNames(), count=count, value=start, scale=scale)

    p.save()

    pdf_out = output.getvalue()
    output.close()

    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename='"+code+"_"+str(start)+"_"+str(count)+".pdf"
    response.mimetype = 'application/pdf'
    return response

@app.route('/i/<code>/<int:scale>/<path:value>')
def img(code, value, scale):
    try:
        dr = createBarcodeDrawing(code, value=str(value), humanReadable=True)
        dr.renderScale = scale
        d = Drawing(dr.width*scale, dr.height*scale)
        d.add(dr)
        d.renderScale = scale
        response = make_response(d.asString('png'))
        response.mimetype = 'image/png'
        return response
    except:
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'error.png', mimetype='image/png')



@app.route('/<code>/<int:scale>/<path:value>')
def pdf(code, value, scale):
    output = cStringIO.StringIO()

    p = canvas.Canvas(output,pagesize=landscape(A4))
    try:
        genBarcode(code, str(value), p, scale)
    except:
        flash("Error while generating a " + code + ": " + str(sys.exc_info()[0]))
        return render_template('main.html', code=code, codes=getCodeNames(), value=value, scale=scale)

    p.save()

    pdf_out = output.getvalue()
    output.close()

    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename='"+code+"_"+str(value)+".pdf"
    response.mimetype = 'application/pdf'
    return response

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()

